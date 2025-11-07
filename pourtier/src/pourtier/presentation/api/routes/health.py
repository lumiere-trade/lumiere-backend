"""
Health check API routes.

Kubernetes-compatible liveness and readiness probes.
"""

from fastapi import APIRouter, Response, status

from pourtier.infrastructure.monitoring.health_check import (
    PourtierHealthCheck,
)

router = APIRouter(prefix="/health", tags=["health"])

# Singleton health check instance
health_check = PourtierHealthCheck()


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe(response: Response):
    """
    Liveness probe endpoint.

    Used by Kubernetes to determine if pod should be restarted.
    Returns 200 if service is alive, 503 if dead.

    Returns:
        Health status dict
    """
    result = await health_check.check_liveness()

    if result["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(response: Response):
    """
    Readiness probe endpoint.

    Used by Kubernetes to determine if pod should receive traffic.
    Returns 200 if ready, 503 if not ready.

    Checks:
    - Database connectivity
    - Redis connectivity (if enabled)
    - Passeur Bridge availability
    - Courier event bus availability

    Returns:
        Health status dict with dependency checks
    """
    result = await health_check.check_readiness()

    if result["status"] in ("unhealthy", "degraded"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result


@router.get("", status_code=status.HTTP_200_OK)
async def health_check_endpoint(response: Response):
    """
    General health check endpoint (alias for readiness).

    Returns:
        Health status dict
    """
    return await readiness_probe(response)
