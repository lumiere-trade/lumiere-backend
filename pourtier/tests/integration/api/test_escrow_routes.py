"""
Integration tests for Escrow API routes.

Tests escrow endpoints with httpx.AsyncClient and test database.

Usage:
    ENV=test python -m pourtier.tests.integration.api.test_escrow_routes
    laborant pourtier --integration
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import create_async_engine

from pourtier.config.settings import load_config, override_settings
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
from pourtier.domain.services.i_blockchain_verifier import (
    VerifiedTransaction,
)
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from pourtier.main import app
from shared.tests import LaborantTest


class TestEscrowRoutes(LaborantTest):
    """Integration tests for Escrow API routes."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    db: Database = None
    client: httpx.AsyncClient = None
    test_user: User = None
    test_token: str = None
    test_settings = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup test database and client."""
        self.reporter.info("Setting up API integration tests...", context="Setup")

        # 1. Load test config and override global settings
        TestEscrowRoutes.test_settings = load_config("test.yaml")
        override_settings(TestEscrowRoutes.test_settings)

        self.reporter.info("Test settings loaded and applied", context="Setup")

        # 2. Create test database instance
        TestEscrowRoutes.db = Database(
            database_url=TestEscrowRoutes.test_settings.DATABASE_URL, echo=False
        )
        await TestEscrowRoutes.db.connect()

        # 3. Drop and recreate tables
        async with TestEscrowRoutes.db._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        self.reporter.info("Test database tables created", context="Setup")

        # 4. Override FastAPI dependency to use test DB
        async def override_get_db_session():
            """Provide test database session."""
            async with TestEscrowRoutes.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session

        self.reporter.info("Database dependency overridden", context="Setup")

        # 5. Create async client (after all overrides)
        TestEscrowRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        # 6. Create test user with escrow
        await self._create_test_user_with_escrow()

        # 7. Generate test JWT token
        TestEscrowRoutes.test_token = self._generate_test_token()

        self.reporter.info("API integration tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info("Cleaning up API integration tests...", context="Teardown")

        # Close AsyncClient
        if TestEscrowRoutes.client:
            await TestEscrowRoutes.client.aclose()

        # Clear dependency overrides
        app.dependency_overrides.clear()

        # Disconnect database
        if TestEscrowRoutes.db:
            await TestEscrowRoutes.db.disconnect()

        # Drop all tables
        engine = create_async_engine(
            TestEscrowRoutes.test_settings.DATABASE_URL, echo=False
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    def _generate_valid_signature(self, prefix: str = "test") -> str:
        """
        Generate valid 88-character Solana transaction signature.

        Solana signatures are 88 characters (base58 encoded 64 bytes).
        """
        base = prefix + ("A" * 88)
        return base[:88]

    def _generate_mock_block_time(self) -> datetime:
        """Generate mock blockchain timestamp (datetime)."""
        return datetime.utcnow() - timedelta(minutes=5)

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
        """Generate test JWT token using test settings."""
        from pourtier.infrastructure.auth.jwt_handler import create_access_token

        return create_access_token(
            user_id=self.test_user.id,
            wallet_address=self.test_user.wallet_address,
        )

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.test_token}"}

    # ================================================================
    # Initialize Escrow Tests
    # ================================================================

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

        # Generate valid signature
        sig = self._generate_valid_signature("init")
        expected_escrow = "3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki"

        # Mock _derive_escrow_pda to return valid escrow
        with patch(
            "pourtier.application.use_cases.initialize_escrow.InitializeEscrow._derive_escrow_pda",
            return_value=expected_escrow,
        ):
            # Mock blockchain verifier
            with patch(
                "pourtier.di.container.DIContainer.blockchain_verifier"
            ) as mock_verifier:
                mock_instance = AsyncMock()
                mock_instance.verify_transaction.return_value = VerifiedTransaction(
                    signature=sig,
                    is_confirmed=True,
                    sender=created_user.wallet_address,
                    recipient=None,
                    amount=None,
                    token_mint="USDC",
                    block_time=int(self._generate_mock_block_time().timestamp()),
                    slot=12345,
                )
                mock_verifier.__get__ = lambda *args: mock_instance

                response = await self.client.post(
                    "/api/escrow/initialize",
                    json={
                        "tx_signature": sig,
                        "token_mint": "USDC",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 201
        data = response.json()
        assert "escrow_account" in data
        assert data["token_mint"] == "USDC"

        self.reporter.info("Initialize escrow successful", context="Test")

    async def test_initialize_escrow_already_initialized(self):
        """Test initializing already initialized escrow."""
        self.reporter.info(
            "Testing initialize escrow (already initialized)", context="Test"
        )

        # Generate valid signature
        sig = self._generate_valid_signature("reinit")

        # Mock blockchain verifier
        with patch(
            "pourtier.di.container.DIContainer.blockchain_verifier"
        ) as mock_verifier:
            mock_instance = AsyncMock()
            mock_instance.verify_transaction.return_value = VerifiedTransaction(
                signature=sig,
                is_confirmed=True,
                sender=self.test_user.wallet_address,
                recipient="3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki",
                amount=None,
                token_mint="USDC",
                block_time=int(self._generate_mock_block_time().timestamp()),
                slot=12345,
            )
            mock_verifier.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/initialize",
                json={
                    "tx_signature": sig,
                    "token_mint": "USDC",
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()

        self.reporter.info("Already initialized error returned", context="Test")

    # ================================================================
    # Deposit Tests
    # ================================================================

    async def test_deposit_success(self):
        """Test successful deposit."""
        self.reporter.info("Testing deposit (success)", context="Test")

        # Generate valid signature
        sig = self._generate_valid_signature("deposit")

        # Mock blockchain verifier
        with patch(
            "pourtier.di.container.DIContainer.blockchain_verifier"
        ) as mock_verifier:
            mock_instance = AsyncMock()
            mock_instance.verify_transaction.return_value = VerifiedTransaction(
                signature=sig,
                is_confirmed=True,
                sender=self.test_user.wallet_address,
                recipient=self.test_user.escrow_account,
                amount=None,
                token_mint="USDC",
                block_time=int(self._generate_mock_block_time().timestamp()),
                slot=12345,
            )
            mock_verifier.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/deposit",
                json={
                    "amount": "100.0",
                    "tx_signature": sig,
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

        sig = self._generate_valid_signature("unauth_deposit")

        response = await self.client.post(
            "/api/escrow/deposit",
            json={
                "amount": "100.0",
                "tx_signature": sig,
            },
        )

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    # ================================================================
    # Withdraw Tests
    # ================================================================

    async def test_withdraw_success(self):
        """Test successful withdrawal."""
        self.reporter.info("Testing withdraw (success)", context="Test")

        # Generate valid signature
        sig = self._generate_valid_signature("withdraw")

        # Mock blockchain verifier
        with patch(
            "pourtier.di.container.DIContainer.blockchain_verifier"
        ) as mock_verifier:
            mock_instance = AsyncMock()
            mock_instance.verify_transaction.return_value = VerifiedTransaction(
                signature=sig,
                is_confirmed=True,
                sender=self.test_user.escrow_account,
                recipient=self.test_user.wallet_address,
                amount=Decimal("50.0"),
                token_mint="USDC",
                block_time=int(self._generate_mock_block_time().timestamp()),
                slot=12345,
            )
            mock_verifier.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "50.0",
                    "tx_signature": sig,
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

        # Generate valid signature
        sig = self._generate_valid_signature("withdraw_fail")

        # Mock blockchain verifier with large amount
        with patch(
            "pourtier.di.container.DIContainer.blockchain_verifier"
        ) as mock_verifier:
            mock_instance = AsyncMock()
            mock_instance.verify_transaction.return_value = VerifiedTransaction(
                signature=sig,
                is_confirmed=True,
                sender=self.test_user.escrow_account,
                recipient=self.test_user.wallet_address,
                amount=Decimal("1000.0"),
                token_mint="USDC",
                block_time=int(self._generate_mock_block_time().timestamp()),
                slot=12345,
            )
            mock_verifier.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/withdraw",
                json={
                    "amount": "1000.0",
                    "tx_signature": sig,
                },
                headers=self._auth_headers(),
            )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

        self.reporter.info("Insufficient balance error returned", context="Test")

    # ================================================================
    # Get Balance Tests
    # ================================================================

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
        assert data["synced_from_blockchain"] is False

        self.reporter.info("Balance retrieved successfully", context="Test")

    async def test_get_balance_with_sync(self):
        """Test getting balance with blockchain sync."""
        self.reporter.info("Testing get balance (with sync)", context="Test")

        # Mock escrow query service
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

        self.reporter.info("Balance synced from blockchain", context="Test")

    async def test_get_balance_unauthorized(self):
        """Test getting balance without authentication."""
        self.reporter.info("Testing get balance (unauthorized)", context="Test")

        response = await self.client.get("/api/escrow/balance")

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    # ================================================================
    # List Transactions Tests
    # ================================================================

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
