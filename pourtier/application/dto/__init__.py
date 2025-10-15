"""
Data Transfer Objects for Pourtier application layer.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class UserDTO:
    """User data transfer object."""

    id: UUID
    wallet_address: str
    email: Optional[str]
    display_name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionDTO:
    """Subscription data transfer object."""

    id: UUID
    user_id: UUID
    plan_type: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class DeployedStrategyDTO:
    """Deployed strategy data transfer object."""

    id: UUID
    user_id: UUID
    strategy_id: UUID
    strategy_name: str
    asset_symbol: str
    asset_interval: str
    escrow_account: Optional[str]
    deposited_amount: Optional[Decimal]
    trading_wallet: Optional[str]
    status: str
    deployed_at: Optional[datetime]
    stopped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class PaymentDTO:
    """Payment data transfer object."""

    id: UUID
    user_id: UUID
    subscription_id: Optional[UUID]
    amount: Decimal
    currency: str
    payment_method: str
    external_id: Optional[str]
    tx_signature: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


__all__ = [
    "UserDTO",
    "SubscriptionDTO",
    "DeployedStrategyDTO",
    "PaymentDTO",
]
