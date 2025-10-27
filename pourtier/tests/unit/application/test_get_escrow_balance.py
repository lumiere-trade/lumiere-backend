"""
Unit tests for GetEscrowBalance use case.

Tests escrow balance retrieval with optional blockchain sync.

Usage:
    python -m pourtier.tests.unit.application.test_get_escrow_balance
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock
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
        """Generate valid Base58 wallet address (44 chars)."""
        return "1" * 44

    def _generate_escrow_account(self) -> str:
        """Generate valid escrow PDA address."""
        return "E" * 44

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_get_escrow_balance_success(self):
        """Test successful balance retrieval."""
        self.reporter.info(
            "Testing successful balance retrieval",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()
        expected_balance = Decimal("250.50")

        user = User(id=user_id, wallet_address=wallet)
        user.initialize_escrow(escrow_account=escrow_account)
        user.update_escrow_balance(expected_balance)

        # Mock repository responses
        user_repo.get_by_id.return_value = user

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(
            user_id=user_id,
            sync_from_blockchain=False,
        )

        # Verify
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == expected_balance
        assert result.escrow_account == escrow_account
        assert result.is_initialized is True
        assert result.initialized_at is not None
        assert result.token_mint == "USDC"
        assert result.last_synced_at is None
        user_repo.get_by_id.assert_called_once_with(user_id)
        query_service.get_escrow_balance.assert_not_called()

        self.reporter.info("Balance retrieved successfully", context="Test")

    async def test_get_escrow_balance_with_sync(self):
        """Test balance retrieval with blockchain sync."""
        self.reporter.info(
            "Testing balance retrieval with blockchain sync",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()
        db_balance = Decimal("100.0")
        blockchain_balance = Decimal("150.0")

        user = User(id=user_id, wallet_address=wallet)
        user.initialize_escrow(escrow_account=escrow_account)
        user.update_escrow_balance(db_balance)

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        user_repo.update.return_value = user
        query_service.get_escrow_balance.return_value = blockchain_balance

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(
            user_id=user_id,
            sync_from_blockchain=True,
        )

        # Verify
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == blockchain_balance
        assert result.is_initialized is True
        assert result.last_synced_at is not None
        user_repo.get_by_id.assert_called_once_with(user_id)
        query_service.get_escrow_balance.assert_called_once_with(
            escrow_account
        )
        user_repo.update.assert_called_once()
        assert user.escrow_balance == blockchain_balance

        self.reporter.info("Balance synced from blockchain", context="Test")

    async def test_get_escrow_balance_sync_no_change(self):
        """Test blockchain sync when balance unchanged."""
        self.reporter.info(
            "Testing blockchain sync with no change",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()
        current_balance = Decimal("200.0")

        user = User(id=user_id, wallet_address=wallet)
        user.initialize_escrow(escrow_account=escrow_account)
        user.update_escrow_balance(current_balance)

        # Mock repository responses - same balance
        user_repo.get_by_id.return_value = user
        query_service.get_escrow_balance.return_value = current_balance

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(
            user_id=user_id,
            sync_from_blockchain=True,
        )

        # Verify - no update needed
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == current_balance
        assert result.is_initialized is True
        query_service.get_escrow_balance.assert_called_once_with(
            escrow_account
        )
        user_repo.update.assert_not_called()

        self.reporter.info(
            "No update needed - balance unchanged",
            context="Test",
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

    async def test_get_balance_escrow_not_initialized(self):
        """Test balance retrieval returns status when escrow not initialized."""
        self.reporter.info(
            "Testing escrow not initialized status",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # User without escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(user_id=user_id)

        # Verify - returns status, not error
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == Decimal("0.00")
        assert result.is_initialized is False
        assert result.escrow_account is None
        assert result.initialized_at is None
        self.reporter.info(
            "Escrow not initialized status returned correctly",
            context="Test",
        )

    async def test_get_balance_zero_balance(self):
        """Test retrieving zero balance."""
        self.reporter.info("Testing zero balance retrieval", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data with zero balance
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()

        user = User(id=user_id, wallet_address=wallet)
        user.initialize_escrow(escrow_account=escrow_account)
        # Balance is Decimal("0") by default

        user_repo.get_by_id.return_value = user

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(user_id=user_id)

        # Verify zero balance
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == Decimal("0")
        assert result.is_initialized is True
        self.reporter.info("Zero balance retrieved correctly", context="Test")

    async def test_get_balance_large_amount(self):
        """Test retrieving large balance."""
        self.reporter.info(
            "Testing large balance retrieval",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        query_service = AsyncMock()

        # Create test data with large balance
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()
        large_balance = Decimal("999999.999999")

        user = User(id=user_id, wallet_address=wallet)
        user.initialize_escrow(escrow_account=escrow_account)
        user.update_escrow_balance(large_balance)

        user_repo.get_by_id.return_value = user

        # Execute use case
        use_case = GetEscrowBalance(
            user_repository=user_repo,
            escrow_query_service=query_service,
        )

        result = await use_case.execute(user_id=user_id)

        # Verify large balance
        assert isinstance(result, EscrowBalanceResult)
        assert result.balance == large_balance
        assert result.is_initialized is True
        self.reporter.info("Large balance retrieved correctly", context="Test")


if __name__ == "__main__":
    TestGetEscrowBalance.run_as_main()
