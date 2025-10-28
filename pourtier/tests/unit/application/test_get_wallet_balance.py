"""
Unit tests for GetWalletBalance use case.

Tests wallet balance retrieval from Passeur Bridge.

Usage:
    python -m pourtier.tests.unit.application.test_get_wallet_balance
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock

from pourtier.application.use_cases.get_wallet_balance import (
    GetWalletBalance,
    WalletBalanceResult,
)
from pourtier.domain.exceptions.base import ValidationError
from pourtier.domain.exceptions.blockchain import BridgeError
from shared.tests import LaborantTest


class TestGetWalletBalance(LaborantTest):
    """Unit tests for GetWalletBalance use case."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Helper Methods
    # ================================================================

    def _generate_valid_wallet(self) -> str:
        """Generate valid Base58 wallet address (44 chars)."""
        return "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"

    def _generate_short_wallet(self) -> str:
        """Generate invalid short wallet address."""
        return "short123"

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_get_wallet_balance_success(self):
        """Test successful wallet balance retrieval."""
        self.reporter.info(
            "Testing successful wallet balance retrieval",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data
        wallet_address = self._generate_valid_wallet()
        expected_balance = Decimal("125.50")

        # Mock bridge response
        passeur_bridge.get_wallet_balance.return_value = expected_balance

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        result = await use_case.execute(wallet_address=wallet_address)

        # Verify
        assert isinstance(result, WalletBalanceResult)
        assert result.wallet_address == wallet_address
        assert result.balance == expected_balance
        assert result.token_mint == "USDC"
        passeur_bridge.get_wallet_balance.assert_called_once_with(wallet_address)

        self.reporter.info(
            "Wallet balance retrieved successfully",
            context="Test",
        )

    async def test_get_wallet_balance_zero(self):
        """Test wallet balance retrieval with zero balance."""
        self.reporter.info(
            "Testing zero wallet balance",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data
        wallet_address = self._generate_valid_wallet()
        zero_balance = Decimal("0.00")

        # Mock bridge response
        passeur_bridge.get_wallet_balance.return_value = zero_balance

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        result = await use_case.execute(wallet_address=wallet_address)

        # Verify
        assert isinstance(result, WalletBalanceResult)
        assert result.balance == zero_balance
        assert result.wallet_address == wallet_address

        self.reporter.info("Zero balance retrieved correctly", context="Test")

    async def test_get_wallet_balance_large_amount(self):
        """Test wallet balance retrieval with large amount."""
        self.reporter.info(
            "Testing large wallet balance",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data
        wallet_address = self._generate_valid_wallet()
        large_balance = Decimal("999999.999999")

        # Mock bridge response
        passeur_bridge.get_wallet_balance.return_value = large_balance

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        result = await use_case.execute(wallet_address=wallet_address)

        # Verify
        assert isinstance(result, WalletBalanceResult)
        assert result.balance == large_balance

        self.reporter.info("Large balance retrieved correctly", context="Test")

    async def test_get_wallet_balance_invalid_wallet_empty(self):
        """Test wallet balance fails with empty wallet address."""
        self.reporter.info(
            "Testing invalid wallet address - empty",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        try:
            await use_case.execute(wallet_address="")
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "wallet_address" in str(e)
            passeur_bridge.get_wallet_balance.assert_not_called()
            self.reporter.info(
                "Empty wallet validation error raised correctly",
                context="Test",
            )

    async def test_get_wallet_balance_invalid_wallet_too_short(self):
        """Test wallet balance fails with short wallet address."""
        self.reporter.info(
            "Testing invalid wallet address - too short",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data
        short_wallet = self._generate_short_wallet()

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        try:
            await use_case.execute(wallet_address=short_wallet)
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "wallet_address" in str(e)
            passeur_bridge.get_wallet_balance.assert_not_called()
            self.reporter.info(
                "Short wallet validation error raised correctly",
                context="Test",
            )

    async def test_get_wallet_balance_invalid_wallet_none(self):
        """Test wallet balance fails with None wallet address."""
        self.reporter.info(
            "Testing invalid wallet address - None",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        try:
            await use_case.execute(wallet_address=None)
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "wallet_address" in str(e)
            passeur_bridge.get_wallet_balance.assert_not_called()
            self.reporter.info(
                "None wallet validation error raised correctly",
                context="Test",
            )

    async def test_get_wallet_balance_bridge_error(self):
        """Test wallet balance fails when Passeur Bridge fails."""
        self.reporter.info(
            "Testing Passeur Bridge error handling",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data
        wallet_address = self._generate_valid_wallet()

        # Mock bridge to raise error
        passeur_bridge.get_wallet_balance.side_effect = BridgeError(
            "Failed to connect to Solana RPC"
        )

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        try:
            await use_case.execute(wallet_address=wallet_address)
            assert False, "Should raise BridgeError"
        except BridgeError as e:
            assert "Failed to connect to Solana RPC" in str(e)
            passeur_bridge.get_wallet_balance.assert_called_once_with(wallet_address)
            self.reporter.info(
                "Bridge error propagated correctly",
                context="Test",
            )

    async def test_get_wallet_balance_decimal_precision(self):
        """Test wallet balance preserves decimal precision."""
        self.reporter.info(
            "Testing decimal precision preservation",
            context="Test",
        )

        # Mock dependencies
        passeur_bridge = AsyncMock()

        # Create test data with precise decimal
        wallet_address = self._generate_valid_wallet()
        precise_balance = Decimal("123.456789")

        # Mock bridge response
        passeur_bridge.get_wallet_balance.return_value = precise_balance

        # Execute use case
        use_case = GetWalletBalance(passeur_bridge=passeur_bridge)

        result = await use_case.execute(wallet_address=wallet_address)

        # Verify precision preserved
        assert isinstance(result, WalletBalanceResult)
        assert result.balance == precise_balance
        assert str(result.balance) == "123.456789"

        self.reporter.info(
            "Decimal precision preserved correctly",
            context="Test",
        )


if __name__ == "__main__":
    TestGetWalletBalance.run_as_main()
