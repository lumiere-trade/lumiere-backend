"""
Integration tests for Escrow API routes.

Tests escrow endpoints with httpx.AsyncClient and test database.

Usage:
    laborant pourtier --integration
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx

from pourtier.config.settings import get_settings
from pourtier.di.dependencies import get_db_session
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

        # Create app
        app = create_app(settings)

        async def override_get_db_session():
            async with TestEscrowRoutes.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.reporter.info("Database dependency overridden", context="Setup")

        # Create client
        TestEscrowRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        # Create test user with escrow
        await self._create_test_user_with_escrow()

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
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    def _generate_valid_signature(self, prefix: str = "test") -> str:
        """Generate valid 88-character Solana transaction signature."""
        base = prefix + ("A" * 88)
        return base[:88]

    async def _create_test_user_with_escrow(self):
        """Create test user with initialized escrow."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            user.initialize_escrow(
                escrow_account="3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki",
                token_mint="USDC",
            )
            user.update_escrow_balance(Decimal("500.0"))
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

    async def test_initialize_escrow_success(self):
        """Test successful escrow initialization."""
        self.reporter.info("Testing initialize escrow (success)", context="Test")

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
        signed_tx = "base64_signed_transaction_init"
        expected_escrow = "3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki"

        # Mock _derive_escrow_pda
        with patch(
            "pourtier.application.use_cases.initialize_escrow.InitializeEscrow._derive_escrow_pda",
            return_value=expected_escrow,
        ):
            # Mock passeur bridge
            with patch(
                "pourtier.di.container.DIContainer.passeur_bridge"
            ) as mock_bridge:
                mock_instance = AsyncMock()
                mock_instance.submit_signed_transaction.return_value = sig
                mock_bridge.__get__ = lambda *args: mock_instance

                response = await self.client.post(
                    "/api/escrow/initialize",
                    json={
                        "signed_transaction": signed_tx,
                        "token_mint": "USDC",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 201
        data = response.json()
        assert "escrow_account" in data
        assert data["token_mint"] == "USDC"
        assert "tx_signature" in data

        self.reporter.info("Initialize escrow successful", context="Test")

    async def test_initialize_escrow_already_initialized(self):
        """Test initializing already initialized escrow."""
        self.reporter.info(
            "Testing initialize escrow (already initialized)", context="Test"
        )

        sig = self._generate_valid_signature("reinit")
        signed_tx = "base64_signed_transaction_reinit"

        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.submit_signed_transaction.return_value = sig
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/initialize",
                json={
                    "signed_transaction": signed_tx,
                    "token_mint": "USDC",
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()

        self.reporter.info("Already initialized error returned", context="Test")

    async def test_deposit_success(self):
        """Test successful deposit."""
        self.reporter.info("Testing deposit (success)", context="Test")

        sig = self._generate_valid_signature("deposit")
        signed_tx = "base64_signed_transaction_deposit"

        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.submit_signed_transaction.return_value = sig
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/deposit",
                json={
                    "amount": "100.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "deposit"
        assert Decimal(data["amount"]) == Decimal("100.0")
        assert data["status"] == "confirmed"

        self.reporter.info("Deposit successful", context="Test")

    async def test_deposit_unauthorized(self):
        """Test deposit without authentication."""
        self.reporter.info("Testing deposit (unauthorized)", context="Test")

        signed_tx = "base64_signed_transaction_unauth"

        response = await self.client.post(
            "/api/escrow/deposit",
            json={
                "amount": "100.0",
                "signed_transaction": signed_tx,
            },
        )

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    async def test_withdraw_success(self):
        """Test successful withdrawal."""
        self.reporter.info("Testing withdraw (success)", context="Test")

        sig = self._generate_valid_signature("withdraw")
        signed_tx = "base64_signed_transaction_withdraw"

        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.submit_signed_transaction.return_value = sig
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "50.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "withdraw"
        assert Decimal(data["amount"]) == Decimal("50.0")

        self.reporter.info("Withdrawal successful", context="Test")

    async def test_withdraw_insufficient_balance(self):
        """Test withdrawal with insufficient balance."""
        self.reporter.info("Testing withdraw (insufficient balance)", context="Test")

        sig = self._generate_valid_signature("withdraw_fail")
        signed_tx = "base64_signed_transaction_withdraw_fail"

        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.submit_signed_transaction.return_value = sig
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "1000.0",
                    "signed_transaction": signed_tx,
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

        self.reporter.info("Insufficient balance error returned", context="Test")

    async def test_get_balance_success(self):
        """Test getting escrow balance."""
        self.reporter.info("Testing get balance (success)", context="Test")

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
        assert "initialized_at" in data
        assert data["synced_from_blockchain"] is False
        assert data["is_initialized"] is True
        assert data["escrow_account"] is not None

        self.reporter.info("Balance retrieved successfully", context="Test")

    async def test_get_balance_with_sync(self):
        """Test getting balance with blockchain sync."""
        self.reporter.info("Testing get balance (with sync)", context="Test")

        with patch(
            "pourtier.di.container.DIContainer.escrow_query_service"
        ) as mock_query:
            mock_instance = AsyncMock()
            mock_instance.get_escrow_balance.return_value = Decimal("600.0")
            mock_query.__get__ = lambda *args: mock_instance

            response = await self.client.get(
                "/api/escrow/balance?sync=true",
                headers=self._auth_headers(),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["synced_from_blockchain"] is True
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
