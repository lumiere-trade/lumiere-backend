"""
Unit tests for WithdrawFromEscrow idempotency.

Tests that duplicate withdrawals are prevented by idempotency keys.

Usage:
    python tests/unit/application/test_withdraw_idempotency.py
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
from shared.tests import LaborantTest


class TestWithdrawIdempotency(LaborantTest):
    """Unit tests for withdraw idempotency protection."""

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
    async def test_withdraw_with_idempotency_prevents_duplicate(self, mock_derive_pda):
        """Test that same idempotency key returns cached result."""
        self.reporter.info(
            "Testing idempotency prevents duplicate withdrawal",
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

        # Mock idempotency store
        idempotency_store = AsyncMock()

        # Create test data
        user_id = uuid4()
        self._generate_valid_wallet()
        withdraw_amount = Decimal("50.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_withdraw_idempotency_123"

        # Cached transaction from previous call
        cached_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=withdraw_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock idempotency store to return cached result
        idempotency_store.get_async.return_value = cached_transaction

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=withdraw_amount,
            signed_transaction=signed_transaction,
            idempotency_key=idempotency_key,
        )

        # Verify cached result returned
        assert result == cached_transaction

        # Verify no actual execution happened (CRITICAL for withdrawals)
        user_repo.get_by_id.assert_not_called()
        passeur_bridge.submit_signed_transaction.assert_not_called()
        tx_repo.create.assert_not_called()
        escrow_query_service.get_escrow_balance.assert_not_called()

        # Verify idempotency check was made
        idempotency_store.get_async.assert_called_once_with(idempotency_key)

        self.reporter.info(
            "Idempotency prevented duplicate withdrawal (CRITICAL)",
            context="Test",
        )

    @patch("pourtier.application.use_cases.withdraw_from_escrow.derive_escrow_pda")
    async def test_withdraw_stores_result_for_idempotency(self, mock_derive_pda):
        """Test that successful withdrawal stores result in idempotency store."""
        self.reporter.info(
            "Testing withdrawal stores result for future idempotency",
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

        # Mock idempotency store
        idempotency_store = AsyncMock()
        idempotency_store.get_async.return_value = None  # Cache miss

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        withdraw_amount = Decimal("75.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_withdraw_idempotency_456"

        user = User(id=user_id, wallet_address=wallet)

        # Create expected transactions (PENDING then CONFIRMED)
        pending_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=withdraw_amount,
            token_mint="USDC",
            status=TransactionStatus.PENDING,
        )

        confirmed_transaction = EscrowTransaction(
            id=pending_transaction.id,
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.WITHDRAW,
            amount=withdraw_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")
        tx_repo.get_by_tx_signature.return_value = None
        tx_repo.create.return_value = pending_transaction
        tx_repo.update.return_value = confirmed_transaction
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case
        use_case = WithdrawFromEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=withdraw_amount,
            signed_transaction=signed_transaction,
            idempotency_key=idempotency_key,
        )

        # Verify result is confirmed
        assert result.status == TransactionStatus.CONFIRMED

        # Verify idempotency store was checked and updated
        idempotency_store.get_async.assert_called_once_with(idempotency_key)
        idempotency_store.set_async.assert_called_once_with(
            idempotency_key,
            confirmed_transaction,
            ttl=86400,  # 24 hours
        )

        self.reporter.info(
            "Withdrawal result stored for idempotency",
            context="Test",
        )


if __name__ == "__main__":
    TestWithdrawIdempotency.run_as_main()
