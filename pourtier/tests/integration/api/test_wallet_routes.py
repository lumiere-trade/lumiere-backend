"""
Integration tests for Wallet API routes.

Tests wallet endpoints with httpx.AsyncClient and mocked Passeur Bridge.
No database required since wallet endpoint is stateless.

Usage:
    laborant pourtier --integration
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx

from pourtier.config.settings import get_settings
from pourtier.domain.exceptions.blockchain import BridgeError
from pourtier.main import create_app
from shared.tests import LaborantTest


class TestWalletRoutes(LaborantTest):
    """Integration tests for Wallet API routes."""

    component_name = "pourtier"
    test_category = "integration"

    client: httpx.AsyncClient = None

    async def async_setup(self):
        """Setup test client (no database needed)."""
        self.reporter.info("Setting up wallet API tests...", context="Setup")

        # Load settings
        settings = get_settings()
        self.reporter.info(f"Loaded ENV={settings.ENV}", context="Setup")

        # Create app
        app = create_app(settings)

        # Create client
        TestWalletRoutes.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        self.reporter.info("Wallet API tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test client."""
        self.reporter.info(
            "Cleaning up wallet API tests...", context="Teardown"
        )

        if TestWalletRoutes.client:
            await TestWalletRoutes.client.aclose()

        self.reporter.info("Cleanup complete", context="Teardown")

    def _generate_valid_wallet(self) -> str:
        """Generate valid 44-character wallet address."""
        return "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"

    def _generate_short_wallet(self) -> str:
        """Generate invalid short wallet address."""
        return "short123"

    async def test_get_wallet_balance_success(self):
        """Test successful wallet balance retrieval."""
        self.reporter.info(
            "Testing get wallet balance (success)", context="Test"
        )

        wallet_address = self._generate_valid_wallet()
        expected_balance = Decimal("125.50")

        # Mock Passeur Bridge
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.get_wallet_balance.return_value = expected_balance
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.get(
                f"/api/wallet/balance?wallet={wallet_address}"
            )

        assert response.status_code == 200
        data = response.json()
        assert "wallet_address" in data
        assert "balance" in data
        assert "token_mint" in data
        assert data["wallet_address"] == wallet_address
        assert Decimal(data["balance"]) == expected_balance
        assert data["token_mint"] == "USDC"

        mock_instance.get_wallet_balance.assert_called_once_with(
            wallet_address
        )

        self.reporter.info("Wallet balance retrieved successfully", context="Test")

    async def test_get_wallet_balance_zero(self):
        """Test wallet balance retrieval with zero balance."""
        self.reporter.info(
            "Testing get wallet balance (zero balance)", context="Test"
        )

        wallet_address = self._generate_valid_wallet()
        zero_balance = Decimal("0.00")

        # Mock Passeur Bridge
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.get_wallet_balance.return_value = zero_balance
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.get(
                f"/api/wallet/balance?wallet={wallet_address}"
            )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["balance"]) == zero_balance

        self.reporter.info("Zero balance retrieved correctly", context="Test")

    async def test_get_wallet_balance_missing_wallet_param(self):
        """Test wallet balance fails without wallet parameter."""
        self.reporter.info(
            "Testing get wallet balance (missing wallet param)",
            context="Test",
        )

        response = await self.client.get("/api/wallet/balance")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

        self.reporter.info(
            "Missing wallet parameter error returned", context="Test"
        )

    async def test_get_wallet_balance_invalid_wallet_too_short(self):
        """Test wallet balance fails with invalid short wallet."""
        self.reporter.info(
            "Testing get wallet balance (invalid wallet - too short)",
            context="Test",
        )

        short_wallet = self._generate_short_wallet()

        # Mock Passeur Bridge (won't be called due to validation)
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.get(
                f"/api/wallet/balance?wallet={short_wallet}"
            )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "wallet_address" in data["detail"]

        mock_instance.get_wallet_balance.assert_not_called()

        self.reporter.info(
            "Invalid wallet validation error returned", context="Test"
        )

    async def test_get_wallet_balance_bridge_error(self):
        """Test wallet balance fails when Passeur Bridge fails."""
        self.reporter.info(
            "Testing get wallet balance (bridge error)", context="Test"
        )

        wallet_address = self._generate_valid_wallet()

        # Mock Passeur Bridge to raise error
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.get_wallet_balance.side_effect = BridgeError(
                "Failed to connect to Solana RPC"
            )
            mock_bridge.__get__ = lambda *args: mock_instance

            response = await self.client.get(
                f"/api/wallet/balance?wallet={wallet_address}"
            )

        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert "Failed to get wallet balance" in data["detail"]

        self.reporter.info("Bridge error handled correctly", context="Test")

    async def test_get_wallet_balance_no_auth_required(self):
        """Test wallet balance endpoint does not require authentication."""
        self.reporter.info(
            "Testing get wallet balance (no auth required)", context="Test"
        )

        wallet_address = self._generate_valid_wallet()
        expected_balance = Decimal("100.00")

        # Mock Passeur Bridge
        with patch(
            "pourtier.di.container.DIContainer.passeur_bridge"
        ) as mock_bridge:
            mock_instance = AsyncMock()
            mock_instance.get_wallet_balance.return_value = expected_balance
            mock_bridge.__get__ = lambda *args: mock_instance

            # Call WITHOUT Authorization header
            response = await self.client.get(
                f"/api/wallet/balance?wallet={wallet_address}"
            )

        # Should succeed without auth
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["balance"]) == expected_balance

        self.reporter.info(
            "Public endpoint works without authentication", context="Test"
        )


if __name__ == "__main__":
    TestWalletRoutes.run_as_main()
