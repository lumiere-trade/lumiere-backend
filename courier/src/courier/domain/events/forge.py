"""
Forge service event schemas.

Events published by Forge during background job processing.
"""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

from courier.domain.events.base import BaseEvent


class ForgeJobStartedData(BaseModel):
    """Data schema for forge.job.started event."""

    job_id: str = Field(..., description="Job ID")
    job_type: str = Field(..., description="Job type (e.g., data_sync, backtest)")
    user_id: str = Field(..., description="User ID")
    parameters: Dict[str, Any] = Field(..., description="Job parameters")

    class Config:
        extra = "forbid"  # Strict validation


class ForgeJobProgressData(BaseModel):
    """Data schema for forge.job.progress event."""

    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress 0-1")
    stage: str = Field(..., description="Current stage")
    message: str = Field(..., description="Progress message")

    class Config:
        extra = "forbid"


class ForgeJobCompletedData(BaseModel):
    """Data schema for forge.job.completed event."""

    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    duration_seconds: int = Field(..., description="Duration in seconds")
    result: Dict[str, Any] = Field(..., description="Job result")

    class Config:
        extra = "forbid"


class ForgeJobFailedData(BaseModel):
    """Data schema for forge.job.failed event."""

    job_id: str = Field(..., description="Job ID")
    user_id: str = Field(..., description="User ID")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: str = Field(default="", description="Error details")

    class Config:
        extra = "forbid"


class ForgeJobStartedEvent(BaseEvent):
    """Background job started."""

    type: Literal["forge.job.started"] = "forge.job.started"
    data: ForgeJobStartedData = Field(..., description="Job details")


class ForgeJobProgressEvent(BaseEvent):
    """Job progress update."""

    type: Literal["forge.job.progress"] = "forge.job.progress"
    data: ForgeJobProgressData = Field(..., description="Progress data")


class ForgeJobCompletedEvent(BaseEvent):
    """Job completed successfully."""

    type: Literal["forge.job.completed"] = "forge.job.completed"
    data: ForgeJobCompletedData = Field(..., description="Completion details")


class ForgeJobFailedEvent(BaseEvent):
    """Job failed."""

    type: Literal["forge.job.failed"] = "forge.job.failed"
    data: ForgeJobFailedData = Field(..., description="Failure details")


# Union type
ForgeEvent = (
    ForgeJobStartedEvent
    | ForgeJobProgressEvent
    | ForgeJobCompletedEvent
    | ForgeJobFailedEvent
)
