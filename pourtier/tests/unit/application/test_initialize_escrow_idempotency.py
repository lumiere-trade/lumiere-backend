"""
Unit tests for InitializeEscrow idempotency.

Tests that duplicate initialization is prevented by idempotency keys.

Usage:
    python tests/unit/application/test_initialize_escrow_idempotency.py
    laborant pourtier --unit
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.initialize_escrow import (
    InitializeEscrow,
)
from pourtier.domain.entities.user import User
from shared.tests import LaborantTest


class TestInitializeEscrowIdempotency(LaborantTest):
    """Unit tests for initialize escrow idempotency protection."""

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

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_with_idempotency_prevents_duplicate(
        self, mock_derive_pda
    ):
        """Test that same idempotency key returns cached result."""
        self.reporter.info(
            "Testing idempotency prevents duplicate initialization",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # Mock idempotency store
        idempotency_store = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_initialize_idempotency_123"

        user = User(id=user_id, wallet_address=wallet)

        # Cached result from previous call
        cached_result = (user, tx_signature)

        # Mock idempotency store to return cached result
        idempotency_store.get_async.return_value = cached_result

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result_user, result_signature = await use_case.execute(
            user_id=user_id,
            signed_transaction=signed_transaction,
            token_mint="USDC",
            idempotency_key=idempotency_key,
        )

        # Verify cached result returned
        assert result_user == user
        assert result_signature == tx_signature

        # Verify no actual execution happened (CRITICAL for initialization)
        user_repo.get_by_id.assert_not_called()
        passeur_bridge.submit_signed_transaction.assert_not_called()
        tx_repo.create.assert_not_called()

        # Verify idempotency check was made
        idempotency_store.get_async.assert_called_once_with(idempotency_key)

        self.reporter.info(
            "Idempotency prevented duplicate initialization (CRITICAL)",
            context="Test",
        )

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_stores_result_for_idempotency(
        self, mock_derive_pda
    ):
        """Test that successful initialization stores result."""
        self.reporter.info(
            "Testing initialization stores result for idempotency",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # Mock idempotency store
        idempotency_store = AsyncMock()
        idempotency_store.get_async.return_value = None  # Cache miss

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"
        idempotency_key = "test_initialize_idempotency_456"

        user = User(id=user_id, wallet_address=wallet)

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result_user, result_signature = await use_case.execute(
            user_id=user_id,
            signed_transaction=signed_transaction,
            token_mint="USDC",
            idempotency_key=idempotency_key,
        )

        # Verify result
        assert result_user == user
        assert result_signature == tx_signature

        # Verify idempotency store was checked and updated
        idempotency_store.get_async.assert_called_once_with(idempotency_key)
        idempotency_store.set_async.assert_called_once()

        # Verify stored value
        call_args = idempotency_store.set_async.call_args
        stored_result = call_args[0][1]
        stored_ttl = call_args[1]["ttl"]

        assert stored_result == (user, tx_signature)
        assert stored_ttl == 86400  # 24 hours

        self.reporter.info(
            "Initialization result stored for idempotency",
            context="Test",
        )

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_auto_generates_idempotency_key(
        self, mock_derive_pda
    ):
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

        # Mock idempotency store
        idempotency_store = AsyncMock()
        idempotency_store.get_async.return_value = None  # Cache miss

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88
        program_id = "11111111111111111111111111111111"

        user = User(id=user_id, wallet_address=wallet)

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        passeur_bridge.submit_signed_transaction.return_value = tx_signature

        # Execute use case WITHOUT idempotency_key
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id=program_id,
            idempotency_store=idempotency_store,
        )

        result_user, result_signature = await use_case.execute(
            user_id=user_id,
            signed_transaction=signed_transaction,
            token_mint="USDC",
            # No idempotency_key provided
        )

        # Verify result
        assert result_user == user
        assert result_signature == tx_signature

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
    TestInitializeEscrowIdempotency.run_as_main()
