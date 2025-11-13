"""
Statistics API routes.
Provides operational metrics and statistics about Courier service.
"""

from fastapi import APIRouter, Depends

from courier.di import Container
from courier.presentation.api.dependencies import get_container

router = APIRouter(tags=["stats"])


def get_connection_manager(container: Container = Depends(get_container)):
    """Dependency for connection manager."""
    return container.connection_manager


@router.get("/stats")
def get_stats(connection_manager=Depends(get_connection_manager)):
    """
    Get Courier service statistics.

    Returns operational metrics including:
    - Total active connections
    - Active channels and their subscriber counts
    - Message delivery statistics (future)

    Returns:
        Statistics dict
    """
    channels = connection_manager.get_all_channels()

    return {
        "total_connections": connection_manager.get_total_connections(),
        "active_channels": len(channels),
        "channels": channels,
        "total_messages_sent": 0,  # TODO: Implement message counter
        "limits": {
            "max_total_connections": connection_manager.max_total_connections,
            "max_connections_per_user": connection_manager.max_connections_per_user,
            "max_clients_per_channel": connection_manager.max_clients_per_channel,
        },
    }
