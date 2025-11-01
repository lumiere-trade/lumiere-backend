"""
Unit tests for PrepareDepositToEscrow use case.

Tests prepare deposit transaction generation logic.

Usage:
    python tests/unit/application/test_prepare_deposit_to_escrow.py
    laborant pourtier --unit
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.prepare_deposit_to_escrow import (
    PrepareDepositToEscrow,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from shared.tests import LaborantTest


class TestPrepareDepositToEscrow(LaborantTest):
    """Unit tests for PrepareDepositToEscrow use case."""

    component_name = "pourtier"
    test_category = "unit"

    def _generate_valid_wallet(self) -> str:
        """Generate valid Base58 wallet address."""
        return "kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y"

    def _generate_escrow_account(self) -> str:
        """Generate valid escrow PDA address."""
        return "EscrowPDA1111111111111111111111111111111111"

    @patch("pourtier.application.use_cases.prepare_deposit_to_escrow.derive_escrow_pda")
    async def test_prepare_deposit_success(self, mock_derive_pda):
        """Test successful prepare deposit."""
        self.reporter.info(
            "Testing successful prepare deposit",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        wallet = self._generate_valid_wallet()
        deposit_amount = Decimal("100.0")

        user = User(id=user_id, wallet_address=wallet)

        fake_unsigned_tx = "fake_base64_unsigned_transaction_xyz"

        # Mock repository responses
        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        passeur_bridge.prepare_deposit.return_value = fake_unsigned_tx

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=deposit_amount,
        )

        # Verify
        assert result.transaction == fake_unsigned_tx
        assert result.escrow_account == escrow_account
        assert result.amount == deposit_amount

        user_repo.get_by_id.assert_called_once_with(user_id)
        mock_derive_pda.assert_called_once()
        escrow_query_service.check_escrow_exists.assert_called_once_with(escrow_account)
        passeur_bridge.prepare_deposit.assert_called_once_with(
            user_wallet=wallet,
            escrow_account=escrow_account,
            amount=deposit_amount,
        )

        self.reporter.info("Prepare deposit successful", context="Test")

    async def test_prepare_deposit_user_not_found(self):
        """Test prepare deposit fails if user not found."""
        self.reporter.info("Testing user not found error", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=uuid4(),
                amount=Decimal("100.0"),
            )
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info(
                "User not found error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.prepare_deposit_to_escrow.derive_escrow_pda")
    async def test_prepare_deposit_escrow_not_initialized(self, mock_derive_pda):
        """Test prepare deposit fails if escrow not initialized on blockchain."""
        self.reporter.info(
            "Testing escrow not initialized error",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # User without escrow on blockchain
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = False

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("100.0"),
            )
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "not initialized" in str(e).lower()
            self.reporter.info(
                "Escrow not initialized error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.prepare_deposit_to_escrow.derive_escrow_pda")
    async def test_prepare_deposit_zero_amount(self, mock_derive_pda):
        """Test prepare deposit fails with zero amount."""
        self.reporter.info("Testing zero amount error", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("0.0"),
            )
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "greater than 0" in str(e)
            self.reporter.info(
                "Zero amount error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.prepare_deposit_to_escrow.derive_escrow_pda")
    async def test_prepare_deposit_negative_amount(self, mock_derive_pda):
        """Test prepare deposit fails with negative amount."""
        self.reporter.info("Testing negative amount error", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(
                user_id=user_id,
                amount=Decimal("-10.0"),
            )
            assert False, "Should raise ValidationError"
        except ValidationError as e:
            assert "greater than 0" in str(e)
            self.reporter.info(
                "Negative amount error raised correctly",
                context="Test",
            )

    @patch("pourtier.application.use_cases.prepare_deposit_to_escrow.derive_escrow_pda")
    async def test_prepare_deposit_bridge_returns_transaction(self, mock_derive_pda):
        """Test prepare deposit properly returns bridge transaction."""
        self.reporter.info(
            "Testing bridge transaction return",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        passeur_bridge = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create test data
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        expected_tx = "very_long_base64_encoded_transaction_data_here"

        user_repo.get_by_id.return_value = user
        escrow_query_service.check_escrow_exists.return_value = True
        passeur_bridge.prepare_deposit.return_value = expected_tx

        # Execute use case
        use_case = PrepareDepositToEscrow(
            user_repository=user_repo,
            passeur_bridge=passeur_bridge,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(
            user_id=user_id,
            amount=Decimal("50.0"),
        )

        assert result.transaction == expected_tx
        assert len(result.transaction) > 0

        self.reporter.info(
            "Bridge transaction returned correctly",
            context="Test",
        )


if __name__ == "__main__":
    TestPrepareDepositToEscrow.run_as_main()
