"""
Check subscription status use case.

Validates user's subscription and plan limits.
"""

from dataclasses import dataclass
from uuid import UUID

from pourtier.domain.entities.subscription import Subscription
from pourtier.domain.exceptions import NoActiveSubscriptionError
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)


@dataclass
class CheckSubscriptionCommand:
    """Command to check subscription status."""

    user_id: UUID


@dataclass
class SubscriptionStatusResult:
    """Result of subscription status check."""

    is_active: bool
    subscription: Subscription | None
    max_active_strategies: int
    plan_type: str


class CheckSubscriptionStatus:
    """
    Use case for checking user's subscription status.

    Returns subscription details and plan limits.
    """

    def __init__(self, subscription_repository: ISubscriptionRepository):
        """
        Initialize use case.

        Args:
            subscription_repository: Subscription repository
        """
        self.subscription_repository = subscription_repository

    async def execute(
        self, command: CheckSubscriptionCommand
    ) -> SubscriptionStatusResult:
        """
        Check subscription status.

        Args:
            command: Command with user_id

        Returns:
            Subscription status result

        Raises:
            NoActiveSubscriptionError: If no active subscription found
        """
        # Get active subscription
        subscription = await self.subscription_repository.get_active_by_user(
            command.user_id
        )

        if not subscription:
            raise NoActiveSubscriptionError()

        # Check if truly active (not expired)
        is_active = subscription.is_active()

        if not is_active:
            raise NoActiveSubscriptionError()

        # Get plan limits
        from pourtier.domain.value_objects.subscription_plan import get_plan_details

        plan_details = get_plan_details(subscription.plan_type.value)

        return SubscriptionStatusResult(
            is_active=True,
            subscription=subscription,
            max_active_strategies=plan_details.max_active_strategies,
            plan_type=subscription.plan_type.value,
        )
