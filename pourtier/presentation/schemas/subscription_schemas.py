"""
Subscription request/response schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSubscriptionRequest(BaseModel):
    """Request to create subscription."""

    plan_type: str = Field(..., description="Plan type: free, basic, pro")
    payment_method: str = Field(..., description="Payment method: solana_pay")
    payment_amount: Decimal = Field(..., description="Payment amount", gt=0)
    payment_currency: str = Field(..., description="Currency code")


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""

    id: UUID
    user_id: UUID
    plan_type: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response schema."""

    is_active: bool
    plan_type: str
    max_active_strategies: int
    subscription: Optional[SubscriptionResponse]
