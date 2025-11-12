"""
Health check endpoints.
"""

from fastapi import APIRouter
from shared.health import HealthStatus

from passeur.infrastructure.monitoring.passeur_health_checker import (
    PasseurHealthChecker,
)

router = APIRouter(tags=["health"])

# Health checker instance (will be injected via dependency)
health_checker: PasseurHealthChecker = None


def set_health_checker(checker: PasseurHealthChecker) -> None:
    """Set health checker instance."""
    global health_checker
    health_checker = checker


@router.get("/health")
async def health_check():
    """
    Overall health check.

    Returns:
        Health status and details
    """
    if not health_checker:
        return {"status": "unhealthy", "message": "Health checker not initialized"}

    status = health_checker.check()

    return {
        "status": status.value,
        "service": "passeur",
        "version": "0.1.0",
    }


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.

    Returns:
        Liveness status
    """
    if not health_checker:
        return {"status": "unhealthy"}

    status = health_checker.liveness()

    return {
        "status": status.value,
        "alive": status == HealthStatus.HEALTHY,
    }


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe.

    Returns:
        Readiness status
    """
    if not health_checker:
        return {"status": "unhealthy"}

    status = health_checker.readiness()

    return {
        "status": status.value,
        "ready": status == HealthStatus.HEALTHY,
    }
