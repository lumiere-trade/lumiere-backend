"""
Strategy request/response schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ActivateStrategyRequest(BaseModel):
    """Request to activate strategy."""

    strategy_id: UUID = Field(..., description="Strategy ID from architect")
    strategy_name: str = Field(..., description="Strategy name")
    asset_symbol: str = Field(..., description="Asset symbol (e.g., SOLUSDT)")
    asset_interval: str = Field(..., description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)")
    deposit_amount: Decimal = Field(
        default=Decimal("0"), description="Initial deposit amount", ge=0
    )
    token_mint: str = Field(default="SOL", description="Token mint address")


class DeactivateStrategyRequest(BaseModel):
    """Request to deactivate strategy."""

    reason: str = Field(default="user_requested", description="Reason for deactivation")


class DeployedStrategyResponse(BaseModel):
    """Deployed strategy response schema."""

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

    class Config:
        """Pydantic config."""

        from_attributes = True
