"""
Dashboard events for real-time trading data streaming.

Published by Chevalier to user dashboard channels.
These are lightweight events for high-frequency streaming.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class DashboardCandleEvent(BaseModel):
    """Real-time candle data for dashboard chart."""

    type: str = Field(default="dashboard.candle", frozen=True)
    deployment_id: str = Field(..., description="Strategy deployment ID")
    token_symbol: str = Field(..., description="Trading pair symbol")
    timestamp: str = Field(..., description="Candle timestamp ISO format")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume")


class DashboardIndicatorsEvent(BaseModel):
    """Real-time indicator values for dashboard."""

    type: str = Field(default="dashboard.indicators", frozen=True)
    deployment_id: str = Field(..., description="Strategy deployment ID")
    values: Dict[str, float] = Field(..., description="Indicator name -> value")


class DashboardPositionEvent(BaseModel):
    """Real-time position state for dashboard."""

    type: str = Field(default="dashboard.position", frozen=True)
    deployment_id: str = Field(..., description="Strategy deployment ID")
    has_position: bool = Field(..., description="Whether position is open")
    entry_price: float = Field(default=0, description="Entry price if in position")
    current_price: float = Field(default=0, description="Current market price")
    size: float = Field(default=0, description="Position size")
    unrealized_pnl: float = Field(default=0, description="Unrealized P&L")
    cash_balance: float = Field(..., description="Available cash")
    total_equity: float = Field(..., description="Total account equity")
    realized_pnl: float = Field(default=0, description="Realized P&L")
    total_trades: int = Field(default=0, description="Total trades executed")


class DashboardSignalEvent(BaseModel):
    """Trading signal notification for dashboard."""

    type: str = Field(default="dashboard.signal", frozen=True)
    deployment_id: str = Field(..., description="Strategy deployment ID")
    signal_type: str = Field(..., description="ENTRY or EXIT")
    price: float = Field(..., description="Signal price")
    reasons: List[str] = Field(default_factory=list, description="Signal reasons")
    indicators: Dict[str, float] = Field(
        default_factory=dict, description="Indicator values at signal"
    )


class DashboardErrorEvent(BaseModel):
    """Strategy error notification for dashboard."""

    type: str = Field(default="dashboard.error", frozen=True)
    deployment_id: str = Field(..., description="Strategy deployment ID")
    failure_count: int = Field(..., description="Consecutive failure count")
    last_error: str = Field(..., description="Last error message")


class StrategyErrorEvent(BaseModel):
    """Strategy error event for global channel notifications."""

    type: str = Field(default="strategy.error", frozen=True)
    strategy_id: str = Field(..., description="Strategy ID")
    user_id: str = Field(..., description="User ID")
    failure_count: int = Field(..., description="Consecutive failure count")
    last_error: str = Field(..., description="Last error message")
