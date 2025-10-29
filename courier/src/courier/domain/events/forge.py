"""
Forge service event schemas.

Events published by Forge during background job processing.
"""

from typing import Any, Dict, Literal

from pydantic import Field

from courier.domain.events.base import BaseEvent


class ForgeJobStartedEvent(BaseEvent):
    """
    Background job started.
    """

    type: Literal["forge.job.started"] = "forge.job.started"
    data: Dict[str, Any] = Field(
        ...,
        description="Job details",
        example={
            "job_id": "job_abc123",
            "job_type": "data_sync",
            "user_id": "user_123",
            "parameters": {"source": "birdeye", "symbols": ["SOL/USDC"]},
        },
    )


class ForgeJobProgressEvent(BaseEvent):
    """
    Job progress update.
    """

    type: Literal["forge.job.progress"] = "forge.job.progress"
    data: Dict[str, Any] = Field(
        ...,
        description="Progress data",
        example={
            "job_id": "job_abc123",
            "user_id": "user_123",
            "progress": 0.6,
            "stage": "syncing",
            "message": "Synced 60% of data...",
        },
    )


class ForgeJobCompletedEvent(BaseEvent):
    """
    Job completed successfully.
    """

    type: Literal["forge.job.completed"] = "forge.job.completed"
    data: Dict[str, Any] = Field(
        ...,
        description="Completion details",
        example={
            "job_id": "job_abc123",
            "user_id": "user_123",
            "duration_seconds": 120,
            "result": {"records_synced": 15000},
        },
    )


class ForgeJobFailedEvent(BaseEvent):
    """
    Job failed.
    """

    type: Literal["forge.job.failed"] = "forge.job.failed"
    data: Dict[str, Any] = Field(
        ...,
        description="Failure details",
        example={
            "job_id": "job_abc123",
            "user_id": "user_123",
            "error_code": "SYNC_FAILED",
            "message": "Failed to sync data from Birdeye",
            "details": "API rate limit exceeded",
        },
    )


# Union type
ForgeEvent = (
    ForgeJobStartedEvent
    | ForgeJobProgressEvent
    | ForgeJobCompletedEvent
    | ForgeJobFailedEvent
)
