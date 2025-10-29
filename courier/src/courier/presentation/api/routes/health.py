"""
Health and statistics endpoints with Clean Architecture.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Response, status

from courier.di import Container
from courier.presentation.api.dependencies import get_container
from courier.presentation.schemas import HealthResponse, StatsResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    container: Container = Depends(get_container),
):
    """
    Health check endpoint.

    Returns basic health status and connection metrics.
    Returns 503 Service Unavailable when shutting down.

    Args:
        response: FastAPI response
        container: DI container

    Returns:
        Health status with uptime and connection counts
    """
    shutdown_manager = container.shutdown_manager
    conn_manager = container.connection_manager

    # Check if shutting down
    if shutdown_manager.is_shutting_down():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return HealthResponse(
            status="shutting_down",
            uptime_seconds=container.get_uptime_seconds(),
            total_clients=conn_manager.get_total_connections(),
            channels=conn_manager.get_all_channels(),
            shutdown_info=shutdown_manager.get_shutdown_info(),
        )

    # Normal healthy response
    return HealthResponse(
        uptime_seconds=container.get_uptime_seconds(),
        total_clients=conn_manager.get_total_connections(),
        channels=conn_manager.get_all_channels(),
    )


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(container: Container = Depends(get_container)):
    """
    Detailed statistics endpoint.

    Returns comprehensive runtime statistics including
    connection counts, message counts, and channel details.

    Args:
        container: DI container

    Returns:
        Detailed statistics
    """
    conn_manager = container.connection_manager

    # Build channel details
    channels: Dict[str, Dict[str, Any]] = {}
    for name, count in conn_manager.get_all_channels().items():
        max_clients = container.settings.max_clients_per_channel
        channels[name] = {
            "active_clients": count,
            "max_clients": max_clients if max_clients > 0 else "unlimited",
        }

    return StatsResponse(
        uptime_seconds=container.get_uptime_seconds(),
        total_connections=container.stats["total_connections"],
        total_messages_sent=container.stats["total_messages_sent"],
        total_messages_received=container.stats["total_messages_received"],
        active_clients=conn_manager.get_total_connections(),
        channels=channels,
    )
