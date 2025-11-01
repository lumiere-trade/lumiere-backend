"""
Unit tests for InitializeEscrow use case.

Tests escrow initialization business logic.

Usage:
    python tests/unit/application/test_initialize_escrow.py
    laborant pourtier --unit
"""

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
from shared.tests import LaborantTest


class TestInitializeEscrow(LaborantTest):
    """Unit tests for InitializeEscrow use case."""

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
    async def test_initialize_escrow_success(self, mock_derive_pda):
        """Test successful escrow initialization."""
        self.reporter.info(
            "Testing successful escrow initialization",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        signed_transaction = "base64_signed_transaction_here"
        tx_signature = "5" * 88  # Valid Solana signature
        program_id = "11111111111111111111111111111111"

        user = User(id=user_id, wallet_address=wallet)

        # Mock responses
        user_repo.get_by_id.return_value = user
        user_repo.update.return_value = user
        passeur_bridge.submit_signed_transaction.return_value = tx_signature
        tx_repo.create.return_value = AsyncMock()

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id=program_id,
        )

        result_user, result_signature = await use_case.execute(
            user_id=user_id,
            signed_transaction=signed_transaction,
            token_mint="USDC",
        )

        # Verify
        assert result_signature == tx_signature
        assert result_user.last_blockchain_check is not None
        user_repo.get_by_id.assert_called_once_with(user_id)
        mock_derive_pda.assert_called_once_with(wallet, program_id)
        passeur_bridge.submit_signed_transaction.assert_called_once_with(
            signed_transaction
        )
        user_repo.update.assert_called_once()
        tx_repo.create.assert_called_once()

        self.reporter.info("Escrow initialized successfully", context="Test")

    async def test_initialize_escrow_user_not_found(self):
        """Test initialization fails if user not found."""
        self.reporter.info("Testing user not found error", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=uuid4(),
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info(
                "User not found error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_escrow_already_initialized(self, mock_derive_pda):
        """Test initialization fails if escrow already exists on blockchain."""
        self.reporter.info(
            "Testing escrow already initialized error",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # User exists
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        # Blockchain rejects because account already exists
        passeur_bridge.submit_signed_transaction.side_effect = Exception(
            "Error: Account already in use"
        )

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                signed_transaction="base64_signed_transaction",
            )
            assert False, "Should raise EscrowAlreadyInitializedError"
        except EscrowAlreadyInitializedError as e:
            assert str(user_id) in str(e)
            self.reporter.info(
                "Already initialized error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.initialize_escrow.derive_escrow_pda")
    async def test_initialize_escrow_with_custom_token(self, mock_derive_pda):
        """Test initialization with custom token mint (always USDC now)."""
        self.reporter.info(
            "Testing initialization with token mint",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        tx_repo = AsyncMock()
        passeur_bridge = AsyncMock()

        # Create test data
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        signed_transaction = "base64_signed_transaction"
        tx_signature = "5" * 88

        user_repo.get_by_id.return_value = user
        user_repo.update.return_value = user
        passeur_bridge.submit_signed_transaction.return_value = tx_signature
        tx_repo.create.return_value = AsyncMock()

        # Execute use case
        use_case = InitializeEscrow(
            user_repository=user_repo,
            escrow_transaction_repository=tx_repo,
            passeur_bridge=passeur_bridge,
            program_id="11111111111111111111111111111111",
        )

        result_user, result_signature = await use_case.execute(
            user_id=user_id,
            signed_transaction=signed_transaction,
            token_mint="USDC",  # Token mint passed but hardcoded in transaction
        )

        # Verify
        assert result_signature == tx_signature
        assert result_user.last_blockchain_check is not None
        self.reporter.info(
            "Initialization successful with token mint",
            context="Test",
        )


if __name__ == "__main__":
    TestInitializeEscrow.run_as_main()
