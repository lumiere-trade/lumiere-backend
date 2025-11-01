"""
Health and statistics endpoints with Clean Architecture.

Provides multiple types of health checks:
1. /health - Simple health check (backward compatible)
2. /health/detailed - Detailed health information with component breakdown
3. /health/live - Liveness probe (is the service running?)
4. /health/ready - Readiness probe (can the service accept traffic?)
"""

from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, Response, status

from courier.di import Container
from courier.presentation.api.dependencies import get_container
from courier.presentation.schemas import (
    ComponentHealth,
    DetailedHealthResponse,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    StatsResponse,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    container: Container = Depends(get_container),
):
    """
    Simple health check endpoint (backward compatible).

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


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    response: Response,
    container: Container = Depends(get_container),
):
    """
    Detailed health check endpoint.

    Returns comprehensive health information including:
    - Overall service status
    - Individual component health (websocket, rate_limiter, connection_manager)
    - Connection statistics (total, per-channel, per-user limits)
    - Rate limiting statistics (hits, rejections)
    - System resources (memory, CPU if available)
    - Uptime information

    Returns 503 Service Unavailable when shutting down.

    Args:
        response: FastAPI response
        container: DI container

    Returns:
        Detailed health status with component breakdown
    """
    shutdown_manager = container.shutdown_manager
    conn_manager = container.connection_manager

    # Determine overall status
    if shutdown_manager.is_shutting_down():
        overall_status = "shutting_down"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        overall_status = "healthy"

    # Build component health statuses
    components = {}

    # WebSocket Server component
    total_connections = conn_manager.get_total_connections()
    max_connections = container.settings.max_total_connections

    ws_status = "healthy"
    ws_message = f"{total_connections} active connections"

    if max_connections > 0 and total_connections >= max_connections * 0.9:
        ws_status = "degraded"
        ws_message = (
            f"Approaching connection limit ({total_connections}/{max_connections})"
        )

    components["websocket_server"] = ComponentHealth(
        status=ws_status,
        message=ws_message,
        details={
            "active_connections": total_connections,
            "max_connections": max_connections if max_connections > 0 else "unlimited",
            "active_channels": len(conn_manager.channels),
        },
    )

    # Rate Limiter component
    rate_limiter = container.websocket_rate_limiter
    rate_limit_hits = container.stats.get("rate_limit_hits", 0)

    rl_status = "healthy"
    rl_message = "Rate limiting operational"

    if rate_limit_hits > 1000:
        rl_status = "degraded"
        rl_message = f"High rate limit hits ({rate_limit_hits})"

    rl_details = {
        "enabled": container.settings.rate_limit_enabled,
        "total_hits": rate_limit_hits,
    }

    if rate_limiter:
        rl_details["global_limit"] = rate_limiter.limit
        rl_details["window_seconds"] = int(rate_limiter.window.total_seconds())
        rl_details["configured_types"] = rate_limiter.get_configured_types()

    components["rate_limiter"] = ComponentHealth(
        status=rl_status,
        message=rl_message,
        details=rl_details,
    )

    # Connection Manager component
    connection_rejections = container.stats.get("connection_rejections", 0)

    cm_status = "healthy"
    cm_message = "Connection management operational"

    if connection_rejections > 100:
        cm_status = "degraded"
        cm_message = f"High connection rejections ({connection_rejections})"

    components["connection_manager"] = ComponentHealth(
        status=cm_status,
        message=cm_message,
        details={
            "total_rejections": connection_rejections,
            "rejections_by_type": container.stats.get(
                "connection_rejections_by_type", {}
            ),
            "max_total": container.settings.max_total_connections,
            "max_per_user": container.settings.max_connections_per_user,
            "max_per_channel": container.settings.max_clients_per_channel,
        },
    )

    # Shutdown Manager component
    if shutdown_manager.is_shutting_down():
        components["shutdown_manager"] = ComponentHealth(
            status="shutting_down",
            message="Graceful shutdown in progress",
            details=shutdown_manager.get_shutdown_info(),
        )
    else:
        components["shutdown_manager"] = ComponentHealth(
            status="healthy",
            message="Ready for shutdown signals",
            details={
                "shutdown_timeout": container.settings.shutdown_timeout,
                "grace_period": container.settings.shutdown_grace_period,
            },
        )

    # Connection statistics
    connections = {
        "total_connections_since_start": container.stats.get("total_connections", 0),
        "active_connections": total_connections,
        "channels": conn_manager.get_all_channels(),
        "channel_count": len(conn_manager.channels),
    }

    # Rate limiting statistics
    rate_limiting = {
        "enabled": container.settings.rate_limit_enabled,
        "total_hits": rate_limit_hits,
        "hits_per_type": container.stats.get("rate_limit_hits_per_type", {}),
        "connection_rejections": connection_rejections,
        "rejections_by_type": container.stats.get("connection_rejections_by_type", {}),
    }

    # System resources
    process = psutil.Process()
    memory_info = process.memory_info()

    system = {
        "memory": {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2),
        },
        "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
        "threads": process.num_threads(),
        "open_files": len(process.open_files()),
    }

    return DetailedHealthResponse(
        status=overall_status,
        uptime_seconds=container.get_uptime_seconds(),
        components=components,
        connections=connections,
        rate_limiting=rate_limiting,
        system=system,
    )


@router.get("/health/live", response_model=LivenessResponse)
async def liveness_check(
    response: Response,
    container: Container = Depends(get_container),
):
    """
    Liveness probe endpoint for Kubernetes.

    Indicates whether the service is alive and should not be restarted.
    This is a simple check - if the endpoint responds, the service is alive.

    Returns 200 OK if alive, 503 Service Unavailable if dead.

    Use this for:
    - Kubernetes liveness probe
    - Detecting deadlocks or hung processes
    - Automatic restart triggers

    Args:
        response: FastAPI response
        container: DI container

    Returns:
        Liveness status
    """
    # Simple liveness check - if we can respond, we're alive
    # Even during shutdown, we're still "alive" (just shutting down gracefully)

    return LivenessResponse(
        alive=True,
        uptime_seconds=container.get_uptime_seconds(),
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(
    response: Response,
    container: Container = Depends(get_container),
):
    """
    Readiness probe endpoint for Kubernetes.

    Indicates whether the service is ready to accept traffic.
    Returns 200 OK when ready, 503 Service Unavailable when not ready.

    Service is NOT ready when:
    - Shutting down (graceful shutdown in progress)
    - Connection limits reached (cannot accept new connections)
    - Critical components unhealthy

    Use this for:
    - Kubernetes readiness probe
    - Load balancer health checks
    - Traffic routing decisions

    Args:
        response: FastAPI response
        container: DI container

    Returns:
        Readiness status with individual checks
    """
    shutdown_manager = container.shutdown_manager
    conn_manager = container.connection_manager

    checks = {}
    ready = True
    message = "Service ready to accept traffic"

    # Check 1: Not shutting down
    checks["not_shutting_down"] = not shutdown_manager.is_shutting_down()
    if shutdown_manager.is_shutting_down():
        ready = False
        message = "Service is shutting down"

    # Check 2: Connection capacity available
    total_connections = conn_manager.get_total_connections()
    max_connections = container.settings.max_total_connections

    if max_connections > 0:
        # Consider ready if under 95% capacity
        checks["connection_capacity"] = total_connections < (max_connections * 0.95)
        if not checks["connection_capacity"]:
            ready = False
            message = (
                f"Connection capacity exhausted ({total_connections}/{max_connections})"
            )
    else:
        checks["connection_capacity"] = True

    # Check 3: Rate limiter operational
    checks["rate_limiter_operational"] = True
    if container.settings.rate_limit_enabled:
        rate_limiter = container.websocket_rate_limiter
        checks["rate_limiter_operational"] = rate_limiter is not None

    # Check 4: Connection manager operational
    checks["connection_manager_operational"] = conn_manager is not None

    # Set appropriate status code
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=ready,
        message=message,
        checks=checks,
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
