"""
Unit tests for WithdrawFromEscrow use case.

Tests withdrawal submission and transaction recording logic.

Usage:
    python tests/unit/application/test_withdraw_from_escrow.py
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.withdraw_from_escrow import (
    WithdrawFromEscrow,
)
from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import (
    EntityNotFoundError,
    InsufficientEscrowBalanceError,
    InvalidTransactionError,
    ValidationError,
)
from shared.tests import LaborantTest


class TestWithdrawFromEscrow(LaborantTest):
    """Unit tests for WithdrawFromEscrow use case."""

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

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_from_escrow_success(self, mock_derive_pda):
        """Test successful withdrawal from escrow."""
        self.reporter.info(
            "Testing successful withdrawal from escrow",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        withdraw_amount = Decimal("50.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88

        # User entity (immutable, no balance)
        user = User(id=user_id, wallet_address=wallet)

        # Create expected transaction
        expected_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=withdraw_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock repository responses - blockchain balance
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")
        tx_repo.get_by_tx_signature.return_value = None
        tx_repo.create.return_value = expected_transaction
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=withdraw_amount,
            signed_transaction=signed_transaction,
        )

        # Verify transaction created correctly
        assert result.transaction_type == TransactionType.WITHDRAW
        assert result.amount == withdraw_amount
        assert result.status == TransactionStatus.CONFIRMED
        
        # Verify calls
        user_repo.get_by_id.assert_called_once_with(user_id)
        escrow_query_service.check_escrow_exists.assert_called_once()
        escrow_query_service.get_escrow_balance.assert_called_once_with(escrow_account)
        passeur_bridge.submit_signed_transaction.assert_called_once_with(
            signed_transaction
        )
        tx_repo.create.assert_called_once()
        
        # User is immutable - no update
        user_repo.update.assert_not_called()

        self.reporter.info("Withdrawal successful", context="Test")

    async def test_withdraw_user_not_found(self):
        """Test withdrawal fails if user not found."""
        self.reporter.info("Testing user not found error", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=uuid4(),
                amount=Decimal("50.0"),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info(
                "User not found error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_escrow_not_initialized(self, mock_derive_pda):
        """Test withdrawal fails if escrow not initialized on blockchain."""
        self.reporter.info(
            "Testing escrow not initialized error",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User without escrow on blockchain
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = False

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("50.0"),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "Escrow not initialized" in str(e)
            self.reporter.info(
                "Escrow not initialized error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_insufficient_balance(self, mock_derive_pda):
        """Test withdrawal fails with insufficient balance from blockchain."""
        self.reporter.info(
            "Testing insufficient balance error",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with insufficient balance on blockchain
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        user = User(id=user_id, wallet_address=wallet)

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("30.0")

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("50.0"),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise InsufficientEscrowBalanceError"
        except InsufficientEscrowBalanceError as e:
            assert "50.0" in str(e)
            assert "30.0" in str(e)
            self.reporter.info(
                "Insufficient balance error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_duplicate_transaction(self, mock_derive_pda):
        """Test withdrawal fails if transaction already processed."""
        self.reporter.info(
            "Testing duplicate transaction error",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # Existing transaction
        tx_signature = "5" * 88
        existing_tx = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=Decimal("50.0"),
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")
        passeur_bridge.submit_signed_transaction.return_value = tx_signature
        tx_repo.get_by_tx_signature.return_value = existing_tx

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("50.0"),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise InvalidTransactionError"
        except InvalidTransactionError as e:
            assert "already processed" in str(e)
            self.reporter.info(
                "Duplicate transaction error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_negative_amount(self, mock_derive_pda):
        """Test withdrawal fails with negative amount."""
        self.reporter.info("Testing negative amount error", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        user = User(id=user_id, wallet_address=wallet)

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("-10.0"),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "must be positive" in str(e)
            self.reporter.info(
                "Negative amount error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_all_balance(self, mock_derive_pda):
        """Test withdrawing entire balance."""
        self.reporter.info("Testing withdraw all balance", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        total_balance = Decimal("100.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88

        # User entity (immutable)
        user = User(id=user_id, wallet_address=wallet)

        # Create expected transaction
        expected_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=total_balance,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock repository responses - blockchain has full balance
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = total_balance
        tx_repo.get_by_tx_signature.return_value = None
        tx_repo.create.return_value = expected_transaction
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=total_balance,
            signed_transaction=signed_transaction,
        )

        # Verify transaction for full amount
        assert result.amount == total_balance
        assert result.transaction_type == TransactionType.WITHDRAW
        
        # Verify blockchain was queried
        escrow_query_service.get_escrow_balance.assert_called_once_with(escrow_account)
        
        # User is immutable - no update
        user_repo.update.assert_not_called()
        
        self.reporter.info("Withdraw all balance successful", context="Test")


if __name__ == "__main__":
    TestWithdrawFromEscrow.run_as_main()
