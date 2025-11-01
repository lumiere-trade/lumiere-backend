"""
Schemas for health and statistics endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    """Health status for individual component."""

    status: str = Field(..., description="Component status (healthy, degraded, unhealthy)")
    message: Optional[str] = Field(None, description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class HealthResponse(BaseModel):
    """
    Basic health check response schema.

    Used for simple health checks and Kubernetes liveness probe.
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


class DetailedHealthResponse(BaseModel):
    """
    Detailed health check response with component breakdown.

    Provides comprehensive health information including:
    - Overall service status
    - Individual component health
    - Connection statistics
    - Rate limiting statistics
    - Memory usage
    - Uptime information
    """

    status: str = Field(..., description="Overall service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    version: str = Field(default="1.0.0", description="Service version")

    # Component health
    components: Dict[str, ComponentHealth] = Field(
        ..., description="Health status per component"
    )

    # Connection statistics
    connections: Dict[str, Any] = Field(..., description="Connection statistics")

    # Rate limiting statistics
    rate_limiting: Dict[str, Any] = Field(..., description="Rate limiting statistics")

    # System resources
    system: Dict[str, Any] = Field(..., description="System resource usage")


class ReadinessResponse(BaseModel):
    """
    Readiness probe response for Kubernetes.

    Indicates whether service is ready to accept traffic.
    """

    ready: bool = Field(..., description="Service readiness status")
    message: Optional[str] = Field(None, description="Readiness message")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")


class LivenessResponse(BaseModel):
    """
    Liveness probe response for Kubernetes.

    Indicates whether service is alive and should not be restarted.
    """

    alive: bool = Field(..., description="Service liveness status")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")


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
