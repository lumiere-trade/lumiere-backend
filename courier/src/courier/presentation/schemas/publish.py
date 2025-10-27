"""
Schemas for event publishing endpoints.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """
    Request schema for publishing events.

    Used by POST /publish endpoint.
    """

    channel: str = Field(..., description="Target channel name")
    data: Dict[str, Any] = Field(..., description="Event payload")


class PublishResponse(BaseModel):
    """
    Response schema for event publishing.
    """

    status: str = Field(default="published")
    channel: str = Field(..., description="Channel name")
    clients_reached: int = Field(..., description="Number of clients reached")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
