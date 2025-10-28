"""
DTOs for event publishing.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator


class PublishEventRequest(BaseModel):
    """
    Request DTO for publishing an event.

    Attributes:
        channel: Target channel name
        data: Event payload
    """

    channel: str = Field(..., description="Target channel name")
    data: Dict[str, Any] = Field(..., description="Event payload")

    @field_validator("channel")
    @classmethod
    def validate_channel_not_empty(cls, v: str) -> str:
        """Validate channel is not empty."""
        if not v or not v.strip():
            raise ValueError("Channel name cannot be empty")
        return v


class PublishEventResponse(BaseModel):
    """
    Response DTO for event publishing.

    Attributes:
        status: Publication status
        channel: Channel name
        clients_reached: Number of clients that received the message
        timestamp: Publication timestamp
    """

    status: str = Field(default="published", description="Publication status")
    channel: str = Field(..., description="Channel name")
    clients_reached: int = Field(..., description="Number of clients reached")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Publication timestamp (ISO format)",
    )

    @field_validator("clients_reached")
    @classmethod
    def validate_clients_reached_non_negative(cls, v: int) -> int:
        """Validate clients_reached is non-negative."""
        if v < 0:
            raise ValueError("clients_reached cannot be negative")
        return v
