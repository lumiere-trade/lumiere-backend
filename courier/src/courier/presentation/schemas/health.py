"""
Schemas for health and statistics endpoints.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint.
    """

    status: str = Field(default="healthy")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_clients: int = Field(..., description="Total connected clients")
    channels: Dict[str, int] = Field(
        ..., description="Channel names mapped to subscriber counts"
    )


class StatsResponse(BaseModel):
    """
    Response schema for statistics endpoint.
    """

    uptime_seconds: float = Field(..., description="Server uptime")
    total_connections: int = Field(..., description="Total connections since start")
    total_messages_sent: int = Field(..., description="Total messages sent")
    total_messages_received: int = Field(..., description="Total messages received")
    active_clients: int = Field(..., description="Currently active clients")
    channels: Dict[str, Dict[str, Any]] = Field(..., description="Channel details")
