"""
Subscription domain exceptions.
"""

from pourtier.domain.exceptions.base import PourtierException


class SubscriptionError(PourtierException):
    """Base exception for subscription-related errors."""


class SubscriptionExpiredError(SubscriptionError):
    """Raised when attempting action with expired subscription."""

    def __init__(self):
        super().__init__("Subscription has expired", code="SUBSCRIPTION_EXPIRED")


class SubscriptionLimitExceededError(SubscriptionError):
    """Raised when user exceeds plan limits."""

    def __init__(self, limit_type: str, current: int, maximum: int):
        message = (
            f"Plan limit exceeded: {limit_type} "
            f"(current: {current}, max: {maximum})"
        )
        super().__init__(message, code="LIMIT_EXCEEDED")


class NoActiveSubscriptionError(SubscriptionError):
    """Raised when user has no active subscription."""

    def __init__(self):
        super().__init__("No active subscription found", code="NO_ACTIVE_SUBSCRIPTION")
