"""
Schemas for health and statistics endpoints.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check response schema.
    """

    status: str = Field(default="healthy", description="Service status")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_clients: int = Field(..., description="Total connected clients")
    channels: Dict[str, int] = Field(
        ..., description="Active channels and their client counts"
    )
    shutdown_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Shutdown status information (if shutting down)"
    )


class StatsResponse(BaseModel):
    """
    Detailed statistics response schema.
    """

    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_connections: int = Field(
        ..., description="Total connections since server start"
    )
    total_messages_sent: int = Field(
        ..., description="Total messages sent since server start"
    )
    total_messages_received: int = Field(
        ..., description="Total messages received since server start"
    )
    active_clients: int = Field(..., description="Currently connected clients")
    channels: Dict[str, Dict[str, Any]] = Field(
        ..., description="Channel details with client counts"
    )
