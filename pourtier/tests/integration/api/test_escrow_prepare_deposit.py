"""
Integration tests for Prepare Deposit Escrow API route.

Tests /api/escrow/prepare-deposit endpoint with httpx.AsyncClient and test database.

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


class TestEscrowPrepareDeposit(LaborantTest):
    """Integration tests for Prepare Deposit Escrow API route."""

    component_name = "pourtier"
    test_category = "integration"

    db: Database = None
    client: httpx.AsyncClient = None
    test_user: User = None
    test_token: str = None

    async def async_setup(self):
        """Setup test database and client."""
        self.reporter.info(
            "Setting up prepare deposit API tests...",
            context="Setup",
        )

        # Load settings
        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        # Create database
        TestEscrowPrepareDeposit.db = Database(
            database_url=settings.DATABASE_URL,
            echo=False,
        )
        await TestEscrowPrepareDeposit.db.connect()
        self.reporter.info("Connected to test database", context="Setup")

        # Reset database schema
        await TestEscrowPrepareDeposit.db.reset_schema_for_testing(
            Base.metadata
        )
        self.reporter.info("Database schema reset", context="Setup")

        # Create app
        app = create_app(settings)

        async def override_get_db_session():
            async with TestEscrowPrepareDeposit.db.session() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.reporter.info("Database dependency overridden", context="Setup")

        # Create client
        TestEscrowPrepareDeposit.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )

        # Create test user with escrow
        await self._create_test_user_with_escrow()

        # Generate token
        TestEscrowPrepareDeposit.test_token = self._generate_test_token()

        self.reporter.info("Prepare deposit API tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test database."""
        self.reporter.info(
            "Cleaning up prepare deposit API tests...",
            context="Teardown",
        )

        if TestEscrowPrepareDeposit.client:
            await TestEscrowPrepareDeposit.client.aclose()

        if TestEscrowPrepareDeposit.db:
            await TestEscrowPrepareDeposit.db.disconnect()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_unique_wallet(self) -> str:
        """Generate unique 44-character wallet address."""
        unique_id = str(uuid4()).replace("-", "")
        return unique_id.ljust(44, "0")

    async def _create_test_user_with_escrow(self):
        """Create test user with initialized escrow."""
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            user = User(wallet_address=self._generate_unique_wallet())
            user.initialize_escrow(
                escrow_account="3aV1Pbb5bT4x7dPdKj2fhgrXM2kPGMsTs4zB7CMkKfki",
                token_mint="USDC",
            )
            user.update_escrow_balance(Decimal("0.0"))
            TestEscrowPrepareDeposit.test_user = await user_repo.create(user)

    def _generate_test_token(self) -> str:
        """Generate test JWT token."""
        from pourtier.infrastructure.auth.jwt_handler import (
            create_access_token,
        )

        return create_access_token(
            user_id=self.test_user.id,
            wallet_address=self.test_user.wallet_address,
        )

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.test_token}"}

    async def test_prepare_deposit_success(self):
        """Test successful prepare deposit."""
        self.reporter.info(
            "Testing prepare deposit (success)",
            context="Test",
        )

        # Mock Passeur Bridge
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.prepare_deposit.return_value = (
                "fake_base64_unsigned_transaction_abcdef123456"
            )
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/prepare-deposit",
                json={"amount": "5.00"},
                headers=self._auth_headers(),
            )

        assert response.status_code == 200
        data = response.json()
        assert "transaction" in data
        assert data["transaction"] == (
            "fake_base64_unsigned_transaction_abcdef123456"
        )
        assert "escrow_account" in data
        assert data["escrow_account"] == self.test_user.escrow_account
        assert "amount" in data
        assert data["amount"] == "5.00"

        # Verify bridge was called correctly
        mock_instance.prepare_deposit.assert_called_once_with(
            user_wallet=self.test_user.wallet_address,
            escrow_account=self.test_user.escrow_account,
            amount=Decimal("5.00"),
        )

        self.reporter.info("Prepare deposit successful", context="Test")

    async def test_prepare_deposit_unauthorized(self):
        """Test prepare deposit without authentication."""
        self.reporter.info(
            "Testing prepare deposit (unauthorized)",
            context="Test",
        )

        response = await self.client.post(
            "/api/escrow/prepare-deposit",
            json={"amount": "5.00"},
        )

        assert response.status_code == 403

        self.reporter.info("Unauthorized error returned", context="Test")

    async def test_prepare_deposit_escrow_not_initialized(self):
        """Test prepare deposit when escrow not initialized."""
        self.reporter.info(
            "Testing prepare deposit (escrow not initialized)",
            context="Test",
        )

        # Create user without escrow
        async with self.db.session() as session:
            user_repo = UserRepository(session)
            new_user = User(wallet_address=self._generate_unique_wallet())
            created_user = await user_repo.create(new_user)

        # Generate token for new user
        from pourtier.infrastructure.auth.jwt_handler import (
            create_access_token,
        )

        token = create_access_token(
            user_id=created_user.id,
            wallet_address=created_user.wallet_address,
        )

        response = await self.client.post(
            "/api/escrow/prepare-deposit",
            json={"amount": "5.00"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "not initialized" in response.json()["detail"].lower()

        self.reporter.info(
            "Escrow not initialized error returned",
            context="Test",
        )

    async def test_prepare_deposit_invalid_amount_zero(self):
        """Test prepare deposit with zero amount."""
        self.reporter.info(
            "Testing prepare deposit (amount = 0)",
            context="Test",
        )

        response = await self.client.post(
            "/api/escrow/prepare-deposit",
            json={"amount": "0.00"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

        self.reporter.info("Zero amount validation error returned", context="Test")

    async def test_prepare_deposit_invalid_amount_negative(self):
        """Test prepare deposit with negative amount."""
        self.reporter.info(
            "Testing prepare deposit (negative amount)",
            context="Test",
        )

        response = await self.client.post(
            "/api/escrow/prepare-deposit",
            json={"amount": "-5.00"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

        self.reporter.info(
            "Negative amount validation error returned",
            context="Test",
        )

    async def test_prepare_deposit_passeur_bridge_failure(self):
        """Test prepare deposit when Passeur Bridge fails."""
        self.reporter.info(
            "Testing prepare deposit (bridge failure)",
            context="Test",
        )

        from pourtier.domain.exceptions.blockchain import BlockchainError

        # Mock Passeur Bridge to raise error
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.prepare_deposit.side_effect = BlockchainError(
                message="Bridge service unavailable"
            )
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/prepare-deposit",
                json={"amount": "5.00"},
                headers=self._auth_headers(),
            )

        assert response.status_code == 502
        assert "failed to prepare deposit" in response.json()["detail"].lower()

        self.reporter.info("Bridge failure error returned", context="Test")

    async def test_prepare_deposit_large_amount(self):
        """Test prepare deposit with large amount."""
        self.reporter.info(
            "Testing prepare deposit (large amount)",
            context="Test",
        )

        # Mock Passeur Bridge
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.prepare_deposit.return_value = (
                "fake_base64_large_tx"
            )
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.post(
                "/api/escrow/prepare-deposit",
                json={"amount": "10000.50"},
                headers=self._auth_headers(),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "10000.50"

        self.reporter.info("Large amount handled correctly", context="Test")


if __name__ == "__main__":
    TestEscrowPrepareDeposit.run_as_main()
