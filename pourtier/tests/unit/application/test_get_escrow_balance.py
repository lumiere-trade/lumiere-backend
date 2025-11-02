"""
Unit tests for GetEscrowBalance use case.

Tests escrow balance retrieval from blockchain (always real-time).

Usage:
    python tests/unit/application/test_get_escrow_balance.py
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.get_escrow_balance import (
    EscrowBalanceResult,
    GetEscrowBalance,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from shared.tests import LaborantTest


class TestGetEscrowBalance(LaborantTest):
    """Unit tests for GetEscrowBalance use case."""

    component_name = "pourtier"
    test_category = "unit"

    # ================================================================
    # Helper Methods
    # ================================================================

    def _generate_valid_wallet(self) -> str:
        """Generate valid Base58 wallet address."""
        return "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"

    def _generate_escrow_account(self) -> str:
        """Generate valid escrow PDA address."""
        return "EscrowPDA1111111111111111111111111111111111"

    # ================================================================
    # Test Methods
    # ================================================================

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_escrow_balance_success(self, mock_derive_pda):
        """Test successful balance retrieval from blockchain."""
        self.reporter.info(
            "Testing successful balance retrieval from blockchain",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        blockchain_balance = Decimal("250.50")

        # User entity (immutable, no balance)
        user = User(id=user_id, wallet_address=wallet)

        # Mock repository responses - blockchain returns balance
        user_repo.get_by_id.return_value = user
        query_service.check_escrow_exists.return_value = True
        query_service.get_escrow_balance.return_value = blockchain_balance

        # Execute use case (always queries blockchain)
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id=user_id)

        # Verify
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == blockchain_balance
        assert result.escrow_account == escrow_account
        assert result.is_initialized is True
        assert result.token_mint == "USDC"
        assert result.last_synced_at is not None

        # Verify blockchain was queried
        user_repo.get_by_id.assert_called_once_with(user_id)
        query_service.check_escrow_exists.assert_called_once_with(escrow_account)
        query_service.get_escrow_balance.assert_called_once_with(escrow_account)

        # User is immutable - no update
        user_repo.update.assert_not_called()

        self.reporter.info(
            "Balance retrieved from blockchain successfully", context="Test"
        )

    async def test_get_balance_user_not_found(self):
        """Test balance retrieval fails if user not found."""
        self.reporter.info("Testing user not found error", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(user_id=uuid4())
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info(
                "User not found error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_balance_escrow_not_initialized(self, mock_derive_pda):
        """Test balance retrieval returns status when escrow not initialized."""
        self.reporter.info(
            "Testing escrow not initialized status",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # User without escrow on blockchain
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        query_service.check_escrow_exists.return_value = False

        # Execute use case (always queries blockchain)
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id=user_id)

        # Verify - returns status, not error
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == Decimal("0")
        assert result.is_initialized is False
        assert result.escrow_account == escrow_account
        query_service.check_escrow_exists.assert_called_once()

        # No user update - User is immutable
        user_repo.update.assert_not_called()

        self.reporter.info(
            "Escrow not initialized status returned correctly",
            context="Test",
        )

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_balance_zero_balance(self, mock_derive_pda):
        """Test retrieving zero balance from blockchain."""
        self.reporter.info("Testing zero balance retrieval", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()

        # User entity (immutable)
        user = User(id=user_id, wallet_address=wallet)

        user_repo.get_by_id.return_value = user
        query_service.check_escrow_exists.return_value = True
        query_service.get_escrow_balance.return_value = Decimal("0")

        # Execute use case (always queries blockchain)
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id=user_id)

        # Verify zero balance from blockchain
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == Decimal("0")
        assert result.is_initialized is True
        query_service.check_escrow_exists.assert_called_once()
        query_service.get_escrow_balance.assert_called_once()

        self.reporter.info(
            "Zero balance retrieved correctly from blockchain", context="Test"
        )

    @patch("pourtier.application.use_cases.get_escrow_balance.derive_escrow_pda")
    async def test_get_balance_large_amount(self, mock_derive_pda):
        """Test retrieving large balance from blockchain."""
        self.reporter.info(
            "Testing large balance retrieval",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        large_balance = Decimal("999999.999999")

        # User entity (immutable)
        user = User(id=user_id, wallet_address=wallet)

        user_repo.get_by_id.return_value = user
        query_service.check_escrow_exists.return_value = True
        query_service.get_escrow_balance.return_value = large_balance

        # Execute use case (always queries blockchain)
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id=user_id)

        # Verify large balance from blockchain
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == large_balance
        assert result.is_initialized is True
        query_service.check_escrow_exists.assert_called_once()
        query_service.get_escrow_balance.assert_called_once()

        self.reporter.info(
            "Large balance retrieved correctly from blockchain", context="Test"
        )


if __name__ == "__main__":
    TestGetEscrowBalance.run_as_main()
