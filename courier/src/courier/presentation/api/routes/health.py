"""
Health check API routes.

Kubernetes-compatible liveness and readiness probes.
"""

from fastapi import APIRouter, Depends, Response, status

from courier.di import Container
from courier.infrastructure.monitoring import CourierHealthChecker
from courier.presentation.api.dependencies import get_container

router = APIRouter(tags=["health"])


def get_health_checker(container: Container = Depends(get_container)):
    """Dependency for health checker."""
    return CourierHealthChecker(
        settings=container.settings,
        connection_manager=container.connection_manager,
    )


@router.get("/health/live", status_code=status.HTTP_200_OK)
def liveness_probe(
    response: Response,
    health_checker: CourierHealthChecker = Depends(get_health_checker),
):
    """
    Liveness probe endpoint.

    Used by Kubernetes to determine if pod should be restarted.
    Returns 200 if service is alive, 503 if dead.

    Returns:
        Health status dict
    """
    report = health_checker.check_liveness()

    if not report.is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return report.to_dict()


@router.get("/health/ready", status_code=status.HTTP_200_OK)
def readiness_probe(
    response: Response,
    health_checker: CourierHealthChecker = Depends(get_health_checker),
):
    """
    Readiness probe endpoint.

    Used by Kubernetes to determine if pod should receive traffic.
    Returns 200 if ready, 503 if not ready.

    Checks:
    - Connection capacity (not approaching limits)
    - Connection manager operational

    Returns:
        Health status dict with dependency checks
    """
    report = health_checker.check_readiness()

    if not report.is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return report.to_dict()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check_endpoint(
    response: Response,
    health_checker: CourierHealthChecker = Depends(get_health_checker),
):
    """
    General health check endpoint (alias for readiness).

    Returns:
        Health status dict
    """
    return readiness_probe(response, health_checker)
