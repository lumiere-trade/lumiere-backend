"""
Integration tests for Escrow API routes.

Tests escrow endpoints with httpx.AsyncClient and test database.
Mocks external services (passeur) using dependency overrides.

Usage:
    laborant test pourtier --integration
"""

import base64
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
from solders.keypair import Keypair

from pourtier.config.settings import get_settings
from pourtier.di.dependencies import get_db_session, get_passeur_bridge
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from pourtier.main import create_app
from shared.tests import LaborantTest


class TestEscrowRoutes(LaborantTest):
    """Integration tests for Escrow API routes."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None
    client: httpx.AsyncClient = None
    test_user: User = None
    test_token: str = None
    mock_passeur: AsyncMock = None
    escrow_account: str = "3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki"

    async def async_setup(self):
        """Setup test database and client."""
        self.reporter.info("Setting up escrow API tests...", context="Setup")

        # Load settings
        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        # Create database
        TestEscrowRoutes.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await TestEscrowRoutes.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Drop and recreate tables
        await TestEscrowRoutes.db.reset_schema_for_testing(Base.metadata)
        self.reporter.info("Database schema reset", context="Setup")

        # Create mock passeur bridge
        TestEscrowRoutes.mock_passeur = AsyncMock()

        # Create app
        app = create_app(settings)

        # Override dependencies
        async def override_get_db_session():
            async with TestEscrowRoutes.db.session() as session:
                yield session

        def override_get_passeur_bridge():
            return TestEscrowRoutes.mock_passeur

        app.dependency_overrides[get_db_session] = override_get_db_session
        app.dependency_overrides[get_passeur_bridge] = override_get_passeur_bridge
        self.reporter.info("Dependencies overridden", context="Setup")

        # Create client
        TestEscrowRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        # Create test user
        await self._create_test_user()

        # Generate token
        TestEscrowRoutes.test_token = self._generate_test_token()

        self.reporter.info("Escrow API tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up escrow API tests...", context="Teardown")

        if TestEscrowRoutes.client:
            await TestEscrowRoutes.client.aclose()

        if TestEscrowRoutes.db:
            await TestEscrowRoutes.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_unique_wallet(self) -> str:
        """Generate unique valid Solana wallet address."""
        keypair = Keypair()
        return str(keypair.pubkey())

    def _generate_valid_signature(self, prefix: str = "test") -> str:
        """Generate valid 88-character Solana transaction signature."""
        base = prefix + ("A" * 88)
        return base[:88]

    def _generate_valid_signed_tx(self, prefix: str = "test") -> str:
        """Generate valid base64-encoded signed transaction (100+ chars)."""
        # Generate 80 chars which becomes 108 in base64
        data = f"{prefix}_" + ("A" * (80 - len(prefix) - 1))
        return base64.b64encode(data.encode()).decode()

    async def _create_test_user(self):
        """Create test user (immutable, no balance)."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            TestEscrowRoutes.test_user = await user_repo.create(user)

    def _generate_test_token(self) -> str:
        """Generate test JWT token."""
        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        return create_access_token(
            user_id=self.test_user.id,
            wallet_address=self.test_user.wallet_address,
        )

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.test_token}"}

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_escrow_success(self, mock_derive_pda):
        """Test successful escrow initialization."""
        self.reporter.info("Testing initialize escrow (success)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        # Create user without escrow
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            new_user = User(wallet_address=self._generate_unique_wallet())
            created_user = await user_repo.create(new_user)

        # Generate token for new user
        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        token = create_access_token(
            user_id=created_user.id,
            wallet_address=created_user.wallet_address,
        )

        # Generate valid signature and transaction
        sig = self._generate_valid_signature("init")
        signed_tx = self._generate_valid_signed_tx("init")

        # Mock passeur bridge response
        self.mock_passeur.submit_signed_transaction.return_value = sig

        response = await self.client.post(
            "/api/escrow/initialize",
            json={
                "signed_transaction": signed_tx,
                "token_mint": "USDC",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tx_signature" in data
        assert data["tx_signature"] == sig

        self.reporter.info("Initialize escrow successful", context="Test")

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_escrow_already_initialized(self, mock_derive_pda):
        """Test initializing already initialized escrow."""
        self.reporter.info(
            "Testing initialize escrow (already initialized)", context="Test"
        )

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        self._generate_valid_signature("reinit")
        signed_tx = self._generate_valid_signed_tx("reinit")

        # Mock passeur bridge to throw error (account already exists)
        self.mock_passeur.submit_signed_transaction.side_effect = Exception(
            "Error: Account already in use"
        )

        response = await self.client.post(
            "/api/escrow/initialize",
            json={
                "signed_transaction": signed_tx,
                "token_mint": "USDC",
            },
            headers=self._auth_headers(),
        )

        assert (
            response.status_code == 409
        ), f"Expected 409, got {response.status_code}: {response.text}"
        assert "already" in response.json()["detail"].lower()

        # Reset mock for other tests
        self.mock_passeur.submit_signed_transaction.side_effect = None

        self.reporter.info("Already initialized error returned", context="Test")

    @patch("pourtier.application.use_cases.deposit_to_escrow.derive_escrow_pda")
    async def test_deposit_success(self, mock_derive_pda):
        """Test successful deposit."""
        self.reporter.info("Testing deposit (success)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        sig = self._generate_valid_signature("deposit")
        signed_tx = self._generate_valid_signed_tx("deposit")

        # Mock passeur bridge response
        self.mock_passeur.submit_signed_transaction.return_value = sig

        # Mock escrow query service
        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_query_instance = AsyncMock()
            mock_query_instance.check_escrow_exists.return_value = True
            mock_query.__get__ = lambda *args: mock_query_instance

            response = await self.client.post(
                "/api/escrow/deposit",
                json={
                    "amount": "100.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["transaction_type"] == "deposit"
        assert Decimal(data["amount"]) == Decimal("100.0")
        assert data["status"] == "confirmed"

        self.reporter.info("Deposit successful", context="Test")

    async def test_deposit_unauthorized(self):
        """Test deposit without authentication."""
        self.reporter.info("Testing deposit (unauthorized)", context="Test")

        signed_tx = self._generate_valid_signed_tx("unauth")

        response = await self.client.post(
            "/api/escrow/deposit",
            json={
                "amount": "100.0",
                "signed_transaction": signed_tx,
            },
        )

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_success(self, mock_derive_pda):
        """Test successful withdrawal."""
        self.reporter.info("Testing withdraw (success)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        sig = self._generate_valid_signature("withdraw")
        signed_tx = self._generate_valid_signed_tx("withdraw")

        # Mock passeur bridge response
        self.mock_passeur.submit_signed_transaction.return_value = sig

        # Mock escrow query service - sufficient balance
        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_query_instance = AsyncMock()
            mock_query_instance.check_escrow_exists.return_value = True
            mock_query_instance.get_escrow_balance.return_value = Decimal("500.0")
            mock_query.__get__ = lambda *args: mock_query_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "50.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["transaction_type"] == "withdraw"
        assert Decimal(data["amount"]) == Decimal("50.0")

        self.reporter.info("Withdrawal successful", context="Test")

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_insufficient_balance(self, mock_derive_pda):
        """Test withdrawal with insufficient balance from blockchain."""
        self.reporter.info("Testing withdraw (insufficient balance)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        sig = self._generate_valid_signature("withdraw_fail")
        signed_tx = self._generate_valid_signed_tx("withdraw_fail")

        # Mock passeur bridge response
        self.mock_passeur.submit_signed_transaction.return_value = sig

        # Mock escrow query service - insufficient blockchain balance
        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_query_instance = AsyncMock()
            mock_query_instance.check_escrow_exists.return_value = True
            mock_query_instance.get_escrow_balance.return_value = Decimal("50.0")
            mock_query.__get__ = lambda *args: mock_query_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "1000.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert (
            response.status_code == 400
        ), f"Expected 400, got {response.status_code}: {response.text}"
        assert "insufficient" in response.json()["detail"].lower()

        self.reporter.info("Insufficient balance error returned", context="Test")

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_balance_success(self, mock_derive_pda):
        """Test getting escrow balance from blockchain."""
        self.reporter.info("Testing get balance (success)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        # Mock escrow query service (both methods needed)
        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_query_instance = AsyncMock()
            mock_query_instance.check_escrow_exists.return_value = True
            mock_query_instance.get_escrow_balance.return_value = Decimal("500.0")
            mock_query.__get__ = lambda *args: mock_query_instance

            response = await self.client.get(
                "/api/escrow/balance",
                headers=self._auth_headers(),
            )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "token_mint" in data
        assert "is_initialized" in data
        assert "escrow_account" in data
        assert data["is_initialized"] is True
        assert data["escrow_account"] == self.escrow_account

        self.reporter.info("Balance retrieved successfully", context="Test")

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_balance_with_sync(self, mock_derive_pda):
        """Test getting balance with blockchain sync."""
        self.reporter.info("Testing get balance (with sync)", context="Test")

        # Mock PDA derivation
        mock_derive_pda.return_value = (self.escrow_account, 255)

        # Mock escrow query service
        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_query_instance = AsyncMock()
            mock_query_instance.check_escrow_exists.return_value = True
            mock_query_instance.get_escrow_balance.return_value = Decimal("600.0")
            mock_query.__get__ = lambda *args: mock_query_instance

            response = await self.client.get(
                "/api/escrow/balance?sync=true",
                headers=self._auth_headers(),
            )

        assert response.status_code == 200
        data = response.json()
        assert "last_synced_at" in data
        assert data["last_synced_at"] is not None

        self.reporter.info("Balance synced from blockchain", context="Test")

    async def test_get_balance_unauthorized(self):
        """Test getting balance without authentication."""
        self.reporter.info("Testing get balance (unauthorized)", context="Test")

        response = await self.client.get("/api/escrow/balance")

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    async def test_list_transactions_success(self):
        """Test listing escrow transactions."""
        self.reporter.info("Testing list transactions (success)", context="Test")

        response = await self.client.get(
            "/api/escrow/transactions",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)

        self.reporter.info(f"Found {data['total']} transactions", context="Test")

    async def test_list_transactions_filter_by_type(self):
        """Test listing transactions filtered by type."""
        self.reporter.info("Testing list transactions (filtered)", context="Test")

        response = await self.client.get(
            "/api/escrow/transactions?transaction_type=deposit",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["transactions"], list)

        self.reporter.info("Filtered transactions retrieved", context="Test")


if __name__ == "__main__":
    TestEscrowRoutes.run_as_main()
