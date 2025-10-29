"""
Cartographe service event schemas.

Events published by Cartographe during backtesting.
"""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, field_validator

from courier.domain.events.base import BaseEvent


class BacktestStartedData(BaseModel):
    """Data schema for backtest.started event."""
    
    backtest_id: str = Field(..., description="Backtest ID")
    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    strategy_id: str = Field(..., description="Strategy ID")
    parameters: Dict[str, Any] = Field(..., description="Backtest parameters")
    
    class Config:
        extra = "forbid"  # Strict validation


class BacktestProgressData(BaseModel):
    """Data schema for backtest.progress event."""
    
    backtest_id: str = Field(..., description="Backtest ID")
    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress 0-1")
    stage: str = Field(..., description="Current stage")
    message: str = Field(..., description="Progress message")
    
    class Config:
        extra = "forbid"
    
    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """Validate progress is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("progress must be between 0.0 and 1.0")
        return v


class BacktestCompletedData(BaseModel):
    """Data schema for backtest.completed event."""
    
    backtest_id: str = Field(..., description="Backtest ID")
    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    duration_seconds: int = Field(..., description="Duration in seconds")
    summary: Dict[str, Any] = Field(..., description="Results summary")
    
    class Config:
        extra = "forbid"


class BacktestFailedData(BaseModel):
    """Data schema for backtest.failed event."""
    
    backtest_id: str = Field(..., description="Backtest ID")
    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: str = Field(default="", description="Error details")
    
    class Config:
        extra = "forbid"


class BacktestCancelledData(BaseModel):
    """Data schema for backtest.cancelled event."""
    
    backtest_id: str = Field(..., description="Backtest ID")
    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    reason: str = Field(..., description="Cancellation reason")
    progress_at_cancellation: float = Field(..., description="Progress when cancelled")
    
    class Config:
        extra = "forbid"


class BacktestStartedEvent(BaseEvent):
    """Backtest started event."""

    type: Literal["backtest.started"] = "backtest.started"
    data: BacktestStartedData = Field(..., description="Backtest parameters")


class BacktestProgressEvent(BaseEvent):
    """Backtest progress event."""

    type: Literal["backtest.progress"] = "backtest.progress"
    data: BacktestProgressData = Field(..., description="Progress data")


class BacktestCompletedEvent(BaseEvent):
    """Backtest completed successfully event."""

    type: Literal["backtest.completed"] = "backtest.completed"
    data: BacktestCompletedData = Field(..., description="Backtest results")


class BacktestFailedEvent(BaseEvent):
    """Backtest failed event."""

    type: Literal["backtest.failed"] = "backtest.failed"
    data: BacktestFailedData = Field(..., description="Failure details")


class BacktestCancelledEvent(BaseEvent):
    """Backtest cancelled by user event."""

    type: Literal["backtest.cancelled"] = "backtest.cancelled"
    data: BacktestCancelledData = Field(..., description="Cancellation details")


# Union type
CartographeEvent = (
    BacktestStartedEvent
    | BacktestProgressEvent
    | BacktestCompletedEvent
    | BacktestFailedEvent
    | BacktestCancelledEvent
)
