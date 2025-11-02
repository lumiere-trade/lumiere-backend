"""
Unit tests for ValidateUserForDeployment use case.

Tests user validation logic for strategy deployment.

Usage:
    python tests/unit/application/test_validate_user_for_deployment.py
    laborant pourtier --unit
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pourtier.application.use_cases.validate_user_for_deployment import (
    ValidateUserForDeployment,
)
from pourtier.domain.entities.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError
from shared.tests import LaborantTest


class TestValidateUserForDeployment(LaborantTest):
    """Unit tests for ValidateUserForDeployment use case."""

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

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_success_all_valid(self, mock_derive_pda):
        """Test successful validation with all requirements met."""
        self.reporter.info(
            "Testing user validation (all valid)",
            context="Test",
        )

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # Create valid user (immutable, no balance)
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # Create active subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.now() + timedelta(days=30),
        )

        # Mock responses - balance comes from blockchain
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is True
        assert result.can_deploy is True
        assert result.has_subscription is True
        assert result.subscription_plan == "pro"
        assert result.subscription_status == "active"
        assert result.has_escrow is True
        assert result.escrow_account == escrow_account
        assert result.escrow_balance == Decimal("100.0")
        assert len(result.validation_errors) == 0

        # Verify blockchain was queried
        escrow_query_service.get_escrow_balance.assert_called_once_with(escrow_account)

        self.reporter.info("User validation successful", context="Test")

    async def test_validate_user_not_found(self):
        """Test validation fails when user not found."""
        self.reporter.info("Testing user not found", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        try:
            await use_case.execute(uuid4())
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info("User not found error raised", context="Test")

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_no_subscription(self, mock_derive_pda):
        """Test validation with no active subscription."""
        self.reporter.info("Testing no subscription", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with escrow but no subscription (immutable)
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # No subscription
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = None
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_subscription is False
        assert result.subscription_plan is None
        assert "No active subscription found" in result.validation_errors

        self.reporter.info("No subscription error detected", context="Test")

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_subscription_expired(self, mock_derive_pda):
        """Test validation with expired subscription."""
        self.reporter.info("Testing expired subscription", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with escrow (immutable)
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # Expired subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.PRO,
            status=SubscriptionStatus.EXPIRED,
            expires_at=datetime.now() - timedelta(days=1),
        )

        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("100.0")

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_subscription is True
        assert result.subscription_status == "expired"
        assert any("not active" in err for err in result.validation_errors)

        self.reporter.info("Expired subscription detected", context="Test")

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_no_escrow(self, mock_derive_pda):
        """Test validation with no escrow initialized on blockchain."""
        self.reporter.info("Testing no escrow", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User without escrow on blockchain
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # Active subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.now() + timedelta(days=30),
        )

        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription
        escrow_query_service.check_escrow_exists.return_value = False

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_escrow is False
        assert result.escrow_account == escrow_account  # Computed even if not exists
        assert "Escrow not initialized" in result.validation_errors

        self.reporter.info("No escrow error detected", context="Test")

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_insufficient_balance(self, mock_derive_pda):
        """Test validation with zero escrow balance from blockchain."""
        self.reporter.info("Testing insufficient balance", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with escrow (immutable, no balance in entity)
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # Active subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.now() + timedelta(days=30),
        )

        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("0")

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_escrow is True
        assert result.escrow_balance == Decimal("0")
        assert any(
            "Insufficient escrow balance" in err for err in result.validation_errors
        )

        # Verify blockchain was queried
        escrow_query_service.get_escrow_balance.assert_called_once_with(escrow_account)

        self.reporter.info("Insufficient balance detected", context="Test")

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_multiple_errors(self, mock_derive_pda):
        """Test validation with multiple errors."""
        self.reporter.info("Testing multiple validation errors", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User without escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # No subscription
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = None
        escrow_query_service.check_escrow_exists.return_value = False

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify multiple errors
        assert result.is_valid is False
        assert result.can_deploy is False
        assert len(result.validation_errors) >= 2
        assert "No active subscription found" in result.validation_errors
        assert "Escrow not initialized" in result.validation_errors

        self.reporter.info(
            f"Multiple errors detected: {result.validation_errors}",
            context="Test",
        )

    @patch(
        "pourtier.application.use_cases.validate_user_for_deployment.derive_escrow_pda"
    )
    async def test_validate_user_free_plan_valid(self, mock_derive_pda):
        """Test validation with FREE plan (still valid)."""
        self.reporter.info("Testing FREE plan validation", context="Test")

        # Mock PDA derivation
        escrow_account = self._generate_escrow_account()
        mock_derive_pda.return_value = (escrow_account, 255)

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()
        escrow_query_service = AsyncMock()

        # User with escrow (immutable)
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # FREE subscription (no expires_at needed)
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
        )

        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription
        escrow_query_service.check_escrow_exists.return_value = True
        escrow_query_service.get_escrow_balance.return_value = Decimal("50.0")

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
            escrow_query_service=escrow_query_service,
            program_id="11111111111111111111111111111111",
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is True
        assert result.can_deploy is True
        assert result.subscription_plan == "free"

        # Verify blockchain was queried
        escrow_query_service.get_escrow_balance.assert_called_once_with(escrow_account)

        self.reporter.info("FREE plan validated successfully", context="Test")


if __name__ == "__main__":
    TestValidateUserForDeployment.run_as_main()
