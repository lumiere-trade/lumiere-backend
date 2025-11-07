"""
Unit tests for DepositToEscrow idempotency.

Tests that duplicate deposits are prevented by idempotency keys.

Usage:
    python tests/unit/application/test_deposit_idempotency.py
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.deposit_to_escrow import (
    DepositToEscrow,
)
from pourtier.domain.entities.escrow_transaction import (
    EscrowTransaction,
    TransactionStatus,
    TransactionType,
)
from pourtier.domain.entities.user import User
from shared.tests import LaborantTest


class TestDepositIdempotency(LaborantTest):
    """Unit tests for deposit idempotency protection."""

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

    @patch("pourtier.application.use_cases.deposit_to_escrow.derive_escrow_pda")
    async def test_deposit_with_idempotency_prevents_duplicate(self, mock_derive_pda):
        """Test that same idempotency key returns cached result."""
        self.reporter.info(
            "Testing idempotency prevents duplicate deposit",
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
        wallet = self._generate_valid_wallet()
        deposit_amount = Decimal("100.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_idempotency_key_123"

        user = User(id=user_id, wallet_address=wallet)

        # First call - cache miss
        cached_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=deposit_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock idempotency store to return cached result
        idempotency_store.get_async.return_value = cached_transaction

        # Execute use case
        use_case = DepositToEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=deposit_amount,
            signed_transaction=signed_transaction,
            idempotency_key=idempotency_key,
        )

        # Verify cached result returned
        assert result == cached_transaction

        # Verify no actual execution happened
        user_repo.get_by_id.assert_not_called()
        passeur_bridge.submit_signed_transaction.assert_not_called()
        tx_repo.create.assert_not_called()

        # Verify idempotency check was made
        idempotency_store.get_async.assert_called_once_with(idempotency_key)

        self.reporter.info(
            "Idempotency prevented duplicate deposit",
            context="Test",
        )

    @patch("pourtier.application.use_cases.deposit_to_escrow.derive_escrow_pda")
    async def test_deposit_stores_result_for_idempotency(self, mock_derive_pda):
        """Test that successful deposit stores result in idempotency store."""
        self.reporter.info(
            "Testing deposit stores result for future idempotency",
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
        deposit_amount = Decimal("100.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_idempotency_key_456"

        user = User(id=user_id, wallet_address=wallet)

        expected_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=deposit_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        tx_repo.get_by_tx_signature.return_value = None
        tx_repo.create.return_value = expected_transaction
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case
        use_case = DepositToEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=deposit_amount,
            signed_transaction=signed_transaction,
            idempotency_key=idempotency_key,
        )

        # Verify result
        assert result == expected_transaction

        # Verify idempotency store was checked and updated
        idempotency_store.get_async.assert_called_once_with(idempotency_key)
        idempotency_store.set_async.assert_called_once_with(
            idempotency_key,
            expected_transaction,
            ttl=86400,  # 24 hours
        )

        self.reporter.info(
            "Deposit result stored for idempotency",
            context="Test",
        )

    @patch("pourtier.application.use_cases.deposit_to_escrow.derive_escrow_pda")
    async def test_deposit_auto_generates_idempotency_key(self, mock_derive_pda):
        """Test that idempotency key is auto-generated if not provided."""
        self.reporter.info(
            "Testing auto-generation of idempotency key",
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
        deposit_amount = Decimal("50.0")
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"

        user = User(id=user_id, wallet_address=wallet)

        expected_transaction = EscrowTransaction(
            id=uuid4(),
            user_id=user_id,
            tx_signature=tx_signature,
            transaction_type=TransactionType.DEPOSIT,
            amount=deposit_amount,
            token_mint="USDC",
            status=TransactionStatus.CONFIRMED,
        )

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        tx_repo.get_by_tx_signature.return_value = None
        tx_repo.create.return_value = expected_transaction
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case WITHOUT idempotency_key
        use_case = DepositToEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=deposit_amount,
            signed_transaction=signed_transaction,
            # No idempotency_key provided
        )

        # Verify result
        assert result == expected_transaction

        # Verify idempotency store was called (key was auto-generated)
        assert idempotency_store.get_async.called
        assert idempotency_store.set_async.called

        # Verify auto-generated key was used
        call_args = idempotency_store.get_async.call_args[0]
        auto_generated_key = call_args[0]
        assert isinstance(auto_generated_key, str)
        assert len(auto_generated_key) > 0

        self.reporter.info(
            "Idempotency key auto-generated successfully",
            context="Test",
        )


if __name__ == "__main__":
    TestDepositIdempotency.run_as_main()
