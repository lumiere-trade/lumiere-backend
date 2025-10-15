"""
Subscription Data Transfer Objects - Presentation Layer.

DTOs handle HTTP/JSON serialization and validation.
Domain commands are in use case files.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class CreateSubscriptionRequest:
    """
    API request DTO for creating subscription.

    Simplified: Only plan_type required.
    Payment is automatically deducted from escrow.
    """

    plan_type: str  # basic, pro, enterprise


@dataclass
class UpdateSubscriptionRequest:
    """API request DTO for updating subscription."""

    status: str  # cancelled, expired


@dataclass
class SubscriptionResponse:
    """Subscription response DTO for API."""

    id: UUID
    user_id: UUID
    plan_type: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionStatusResponse:
    """Subscription status check response."""

    has_active_subscription: bool
    current_plan: Optional[str] = None
