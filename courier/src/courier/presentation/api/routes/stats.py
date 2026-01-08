"""
Statistics API routes.

Provides operational metrics and statistics about Courier service.
"""

from fastapi import APIRouter, Depends

from courier.di import Container
from courier.presentation.api.dependencies import get_container

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats(container: Container = Depends(get_container)):
    """
    Get Courier service statistics.

    Returns operational metrics including:
    - Total active connections
    - Active channels and their subscriber counts
    - Message delivery statistics

    Returns:
        Statistics dict
    """
    connection_manager = container.connection_manager
    channels = connection_manager.get_all_channels()

    return {
        "total_connections": connection_manager.get_total_connections(),
        "active_channels": len(channels),
        "channels": channels,
        "total_messages_sent": container.stats.get("total_messages_sent", 0),
        "total_messages_received": container.stats.get("total_messages_received", 0),
        "validation_failures": container.stats.get("validation_failures", 0),
        "rate_limit_hits": container.stats.get("rate_limit_hits", 0),
        "limits": {
            "max_total_connections": connection_manager.max_total_connections,
            "max_connections_per_user": connection_manager.max_connections_per_user,
            "max_clients_per_channel": connection_manager.max_clients_per_channel,
        },
    }
