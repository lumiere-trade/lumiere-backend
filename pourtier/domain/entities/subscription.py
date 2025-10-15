"""
Subscription entity - Domain model for user subscriptions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SubscriptionPlan(str, Enum):
    """Available subscription plans."""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle states."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Subscription:
    """
    Subscription entity representing a user's SaaS subscription.

    Business rules:
    - Free plan never expires
    - Paid plans have expiration date
    - Status transitions: active -> cancelled/expired
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    plan_type: SubscriptionPlan = field(default=SubscriptionPlan.FREE)
    status: SubscriptionStatus = field(default=SubscriptionStatus.ACTIVE)
    started_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate subscription data after initialization."""
        if self.plan_type != SubscriptionPlan.FREE and not self.expires_at:
            raise ValueError("Paid plans must have expiration date")

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False

        if self.plan_type == SubscriptionPlan.FREE:
            return True

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        return True

    def cancel(self) -> None:
        """Cancel subscription (user-initiated)."""
        self.status = SubscriptionStatus.CANCELLED
        self.updated_at = datetime.now()

    def expire(self) -> None:
        """Mark subscription as expired (system-initiated)."""
        self.status = SubscriptionStatus.EXPIRED
        self.updated_at = datetime.now()

    def renew(self, duration_days: int) -> None:
        """Renew subscription for specified duration."""
        if self.plan_type == SubscriptionPlan.FREE:
            raise ValueError("Cannot renew free plan")

        self.status = SubscriptionStatus.ACTIVE

        # Extend from now or from current expiration
        base_date = (
            self.expires_at
            if self.expires_at and self.expires_at > datetime.now()
            else datetime.now()
        )

        self.expires_at = base_date + timedelta(days=duration_days)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "plan_type": self.plan_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "expires_at": (self.expires_at.isoformat() if self.expires_at else None),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
