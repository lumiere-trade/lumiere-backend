"""
SubscriptionPlan value object - Immutable subscription plan details.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class SubscriptionPlanDetails:
    """
    Value object representing subscription plan configuration.

    Business rules:
    - Each plan has fixed price and duration
    - Free plan has zero price, unlimited duration
    - Paid plans have monthly/yearly duration
    """

    plan_type: str
    price: Decimal
    duration_days: Optional[int]
    max_active_strategies: int
    features: tuple[str, ...]

    def __post_init__(self):
        """Validate plan details on creation."""
        if not self.plan_type:
            raise ValueError("Plan type is required")

        if self.price < 0:
            raise ValueError("Price cannot be negative")

        if self.duration_days is not None and self.duration_days <= 0:
            raise ValueError("Duration must be positive")

        if self.max_active_strategies <= 0:
            raise ValueError("Max strategies must be positive")

    def is_free(self) -> bool:
        """Check if this is a free plan."""
        return self.price == Decimal("0")

    def monthly_price(self) -> Decimal:
        """Calculate monthly price for comparison."""
        if self.is_free():
            return Decimal("0")

        if self.duration_days is None:
            return Decimal("0")

        # Convert to monthly equivalent
        months = Decimal(self.duration_days) / Decimal("30")
        return self.price / months if months > 0 else self.price

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "plan_type": self.plan_type,
            "price": str(self.price),
            "duration_days": self.duration_days,
            "max_active_strategies": self.max_active_strategies,
            "features": list(self.features),
        }


# Predefined plan configurations
FREE_PLAN = SubscriptionPlanDetails(
    plan_type="free",
    price=Decimal("0"),
    duration_days=None,
    max_active_strategies=1,
    features=(
        "1 active strategy",
        "Basic indicators",
        "Community support",
    ),
)

BASIC_PLAN = SubscriptionPlanDetails(
    plan_type="basic",
    price=Decimal("29.99"),
    duration_days=30,
    max_active_strategies=3,
    features=(
        "3 active strategies",
        "All indicators",
        "Email support",
        "Backtest history",
    ),
)

PRO_PLAN = SubscriptionPlanDetails(
    plan_type="pro",
    price=Decimal("99.99"),
    duration_days=30,
    max_active_strategies=10,
    features=(
        "10 active strategies",
        "All indicators",
        "Priority support",
        "Advanced analytics",
        "Custom alerts",
    ),
)


def get_plan_details(plan_type: str) -> SubscriptionPlanDetails:
    """Get plan details by type."""
    plans = {
        "free": FREE_PLAN,
        "basic": BASIC_PLAN,
        "pro": PRO_PLAN,
    }

    plan = plans.get(plan_type.lower())
    if not plan:
        raise ValueError(f"Unknown plan type: {plan_type}")

    return plan
