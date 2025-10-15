"""
Unit tests for ValidateUserForDeployment use case.

Tests user validation logic for strategy deployment.

Usage:
    python -m pourtier.tests.unit.application.test_validate_user_for_deployment
    laborant pourtier --unit
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
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
        """Generate valid Base58 wallet address (44 chars)."""
        return "1" * 44

    def _generate_escrow_account(self) -> str:
        """Generate valid escrow PDA address."""
        return "E" * 44

    # ================================================================
    # Test Methods
    # ================================================================

    async def test_validate_user_success_all_valid(self):
        """Test successful validation with all requirements met."""
        self.reporter.info(
            "Testing user validation (all valid)",
            context="Test",
        )

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # Create valid user with escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())
        user.update_escrow_balance(Decimal("100.0"))

        # Create active subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.now() + timedelta(days=30),
        )

        # Mock responses
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is True
        assert result.can_deploy is True
        assert result.has_subscription is True
        assert result.subscription_plan == "pro"
        assert result.subscription_status == "active"
        assert result.has_escrow is True
        assert result.escrow_balance == Decimal("100.0")
        assert len(result.validation_errors) == 0

        self.reporter.info("User validation successful", context="Test")

    async def test_validate_user_not_found(self):
        """Test validation fails when user not found."""
        self.reporter.info("Testing user not found", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User not found
        user_repo.get_by_id.return_value = None

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        try:
            await use_case.execute(uuid4())
            assert False, "Should raise EntityNotFoundError"
        except EntityNotFoundError as e:
            assert "User" in str(e)
            self.reporter.info("User not found error raised", context="Test")

    async def test_validate_user_no_subscription(self):
        """Test validation with no active subscription."""
        self.reporter.info("Testing no subscription", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User with escrow but no subscription
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())
        user.update_escrow_balance(Decimal("100.0"))

        # No subscription
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = None

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_subscription is False
        assert result.subscription_plan is None
        assert "No active subscription found" in result.validation_errors

        self.reporter.info("No subscription error detected", context="Test")

    async def test_validate_user_subscription_expired(self):
        """Test validation with expired subscription."""
        self.reporter.info("Testing expired subscription", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User with escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())
        user.update_escrow_balance(Decimal("100.0"))

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

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_subscription is True
        assert result.subscription_status == "expired"
        assert any("not active" in err for err in result.validation_errors)

        self.reporter.info("Expired subscription detected", context="Test")

    async def test_validate_user_no_escrow(self):
        """Test validation with no escrow initialized."""
        self.reporter.info("Testing no escrow", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User without escrow
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

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is False
        assert result.can_deploy is False
        assert result.has_escrow is False
        assert result.escrow_account is None
        assert "Escrow not initialized" in result.validation_errors

        self.reporter.info("No escrow error detected", context="Test")

    async def test_validate_user_insufficient_balance(self):
        """Test validation with zero escrow balance."""
        self.reporter.info("Testing insufficient balance", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User with escrow but zero balance
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())
        user.update_escrow_balance(Decimal("0"))

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

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
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

        self.reporter.info("Insufficient balance detected", context="Test")

    async def test_validate_user_multiple_errors(self):
        """Test validation with multiple errors."""
        self.reporter.info("Testing multiple validation errors", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User without escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())

        # No subscription
        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = None

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
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

    async def test_validate_user_free_plan_valid(self):
        """Test validation with FREE plan (still valid)."""
        self.reporter.info("Testing FREE plan validation", context="Test")

        # Mock dependencies
        user_repo = AsyncMock()
        subscription_repo = AsyncMock()

        # User with escrow
        user_id = uuid4()
        user = User(id=user_id, wallet_address=self._generate_valid_wallet())
        user.initialize_escrow(escrow_account=self._generate_escrow_account())
        user.update_escrow_balance(Decimal("50.0"))

        # FREE subscription (no expires_at needed)
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            plan_type=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
        )

        user_repo.get_by_id.return_value = user
        subscription_repo.get_active_by_user.return_value = subscription

        # Execute use case
        use_case = ValidateUserForDeployment(
            user_repository=user_repo,
            subscription_repository=subscription_repo,
        )

        result = await use_case.execute(user_id)

        # Verify
        assert result.is_valid is True
        assert result.can_deploy is True
        assert result.subscription_plan == "free"

        self.reporter.info("FREE plan validated successfully", context="Test")


if __name__ == "__main__":
    TestValidateUserForDeployment.run_as_main()
