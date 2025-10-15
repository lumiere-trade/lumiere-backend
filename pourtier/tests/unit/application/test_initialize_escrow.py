"""
Unit tests for InitializeEscrow use case.

Tests escrow initialization business logic.

Usage:
    python -m pourtier.tests.unit.application.test_initialize_escrow
    laborant pourtier --unit
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.initialize_escrow import (
    InitializeEscrow,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import (
    EntityNotFoundError,
    EscrowAlreadyInitializedError,
)
from pourtier.domain.services.i_blockchain_verifier import (
    VerifiedTransaction,
)
from shared.tests import LaborantTest


class TestInitializeEscrow(LaborantTest):
    """Unit tests for InitializeEscrow use case."""

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

    async def test_initialize_escrow_success(self):
        """Test successful escrow initialization."""
        self.reporter.info(
            "Testing successful escrow initialization",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        verifier = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        escrow_account = self._generate_escrow_account()
        tx_signature = "tx_sig_123"

        user = User(id=user_id, wallet_address=wallet)

        verified_tx = VerifiedTransaction(
            signature=tx_signature,
            is_confirmed=True,
            sender=wallet,
            recipient=None,  # Not extracted (custom program)
            amount=None,
            token_mint="USDC",
            block_time=int(datetime.now().timestamp()),
            slot=12345,
        )

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        user_repo.update.return_value = user
        verifier.verify_transaction.return_value = verified_tx
        tx_repo.create.return_value = AsyncMock()

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            blockchain_verifier=verifier,
        )

        # Mock _derive_escrow_pda to return expected escrow
        with patch.object(use_case, "_derive_escrow_pda", return_value=escrow_account):
            result = await use_case.execute(
                user_id=user_id,
                tx_signature=tx_signature,
                token_mint="USDC",
            )

        # Verify
        assert result.escrow_account == escrow_account
        assert result.escrow_token_mint == "USDC"
        user_repo.get_by_id.assert_called_once_with(user_id)
        verifier.verify_transaction.assert_called_once_with(tx_signature)
        user_repo.update.assert_called_once()
        tx_repo.create.assert_called_once()

        self.reporter.info("Escrow initialized successfully", context="Test")

    async def test_initialize_escrow_user_not_found(self):
        """Test initialization fails if user not found."""
        self.reporter.info("Testing user not found error", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        verifier = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            blockchain_verifier=verifier,
        )

        try:
            await use_case.execute(
                user_id=uuid4(),
                tx_signature="tx_sig_123",
            )
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info(
                "User not found error raised correctly",
                context="Test",
            )

    async def test_initialize_escrow_already_initialized(self):
        """Test initialization fails if escrow already exists."""
        self.reporter.info(
            "Testing escrow already initialized error",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        verifier = AsyncMock()

        # User with existing escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())

        user_repo.get_by_id.return_value = user

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            blockchain_verifier=verifier,
        )

        try:
            await use_case.execute(
                user_id=user_id,
                tx_signature="tx_sig_123",
            )
            assert False, "Should raise EscrowAlreadyInitializedError"
        except EscrowAlreadyInitializedError as e:
            assert str(user_id) in str(e)
            self.reporter.info(
                "Already initialized error raised correctly",
                context="Test",
            )

    async def test_initialize_escrow_with_custom_token(self):
        """Test initialization with custom token mint."""
        self.reporter.info(
            "Testing initialization with custom token",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        verifier = AsyncMock()

        # Create test data
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        escrow_account = self._generate_escrow_account()

        verified_tx = VerifiedTransaction(
            signature="tx_sig_123",
            is_confirmed=True,
            sender=user.wallet_address,
            recipient=None,
            amount=None,
            token_mint="SOL",
            block_time=int(datetime.now().timestamp()),
            slot=12345,
        )

        user_repo.get_by_id.return_value = user
        user_repo.update.return_value = user
        verifier.verify_transaction.return_value = verified_tx
        tx_repo.create.return_value = AsyncMock()

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            blockchain_verifier=verifier,
        )

        # Mock _derive_escrow_pda
        with patch.object(use_case, "_derive_escrow_pda", return_value=escrow_account):
            result = await use_case.execute(
                user_id=user_id,
                tx_signature="tx_sig_123",
                token_mint="SOL",
            )

        # Verify custom token
        assert result.escrow_token_mint == "SOL"
        self.reporter.info(
            "Custom token initialization successful",
            context="Test",
        )


if __name__ == "__main__":
    TestInitializeEscrow.run_as_main()
