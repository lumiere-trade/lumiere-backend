"""
Base event schemas for Courier event validation.

All events must inherit from BaseEvent to ensure consistent structure.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    """
    Metadata common to all events.

    Attributes:
        timestamp: ISO 8601 timestamp
        source: Publishing service name
        correlation_id: Optional trace ID for request tracking
        user_id: Optional user ID (for user-scoped events)
    """

    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp with Z suffix",
    )
    source: str = Field(..., description="Publishing service name")
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for distributed tracing",
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID for user-scoped events",
    )


class BaseEvent(BaseModel):
    """
    Base event that all Courier events must inherit from.

    Provides:
    - Consistent structure (type, metadata, data)
    - Automatic timestamp generation
    - Source validation
    - Type safety via Pydantic

    Attributes:
        type: Event type identifier (e.g., 'backtest.started')
        metadata: Event metadata (timestamp, source, etc.)
        data: Event-specific payload
    """

    type: str = Field(..., description="Event type identifier")
    metadata: EventMetadata = Field(..., description="Event metadata")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}
        # Allow extra fields for forward compatibility
        extra = "allow"

    def get_channel(self) -> Optional[str]:
        """
        Determine target channel from event data.

        Returns:
            Channel name, or None if cannot be determined
        """
        # User-scoped events
        if self.metadata.user_id:
            return f"user.{self.metadata.user_id}"

        # Strategy-scoped events
        if "strategy_id" in self.data:
            return f"strategy.{self.data['strategy_id']}"

        # Backtest-scoped events
        if "backtest_id" in self.data:
            return f"backtest.{self.data['backtest_id']}"

        # Job-scoped events
        if "job_id" in self.data:
            return f"forge.job.{self.data['job_id']}"

        # Default to global channel
        return "global"
