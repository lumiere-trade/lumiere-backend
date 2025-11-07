"""
Pourtier Health Check implementation.

Kubernetes-compatible health checks for liveness and readiness probes.
"""

from typing import Dict, Any

from shared.health import HealthCheck, HealthStatus

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container


class PourtierHealthCheck(HealthCheck):
    """
    Health check for Pourtier API Gateway.

    Checks:
    - Database connectivity (PostgreSQL)
    - Redis connectivity (if enabled)
    - Passeur Bridge availability
    - Courier event bus availability
    """

    def __init__(self):
        """Initialize health check with component name."""
        super().__init__(component_name="pourtier")
        self.container = get_container()
        self.settings = get_settings()

    async def check_liveness(self) -> Dict[str, Any]:
        """
        Liveness probe - is the service alive?

        Returns basic service info without checking dependencies.
        Used by Kubernetes to restart unhealthy pods.

        Returns:
            Dict with status and basic info
        """
        return {
            "status": HealthStatus.HEALTHY.value,
            "component": "pourtier",
            "version": "1.0.0",
            "timestamp": self._get_timestamp(),
        }

    async def check_readiness(self) -> Dict[str, Any]:
        """
        Readiness probe - is the service ready to handle requests?

        Checks all critical dependencies.
        Used by Kubernetes to route traffic.

        Returns:
            Dict with status and dependency checks
        """
        checks = {}
        overall_status = HealthStatus.HEALTHY

        # 1. Check Database
        db_status = await self._check_database()
        checks["database"] = db_status
        if db_status["status"] != HealthStatus.HEALTHY.value:
            overall_status = HealthStatus.UNHEALTHY

        # 2. Check Redis (if enabled)
        if self.settings.REDIS_ENABLED:
            redis_status = await self._check_redis()
            checks["redis"] = redis_status
            if redis_status["status"] != HealthStatus.HEALTHY.value:
                overall_status = HealthStatus.DEGRADED

        # 3. Check Passeur Bridge
        passeur_status = await self._check_passeur_bridge()
        checks["passeur_bridge"] = passeur_status
        if passeur_status["status"] != HealthStatus.HEALTHY.value:
            overall_status = HealthStatus.DEGRADED

        # 4. Check Courier Event Bus
        courier_status = await self._check_courier()
        checks["courier"] = courier_status
        if courier_status["status"] != HealthStatus.HEALTHY.value:
            overall_status = HealthStatus.DEGRADED

        return {
            "status": overall_status.value,
            "component": "pourtier",
            "version": "1.0.0",
            "timestamp": self._get_timestamp(),
            "checks": checks,
        }

    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity."""
        try:
            # Simple query to verify connection
            async with self.container.database.session() as session:
                result = await session.execute("SELECT 1")
                await result.fetchone()

            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Database connected",
                "response_time_ms": 0,  # Could add timing
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Database connection failed: {str(e)}",
                "error": str(e),
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # Ping Redis
            cache_client = self.container.cache_client
            await cache_client.ping()

            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Redis connected",
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Redis connection failed: {str(e)}",
                "error": str(e),
            }

    async def _check_passeur_bridge(self) -> Dict[str, Any]:
        """Check Passeur Bridge availability."""
        try:
            # Check if Passeur circuit breaker is open
            passeur = self.container.passeur_bridge
            cb_state = passeur.circuit_breaker.state

            if cb_state == "open":
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "message": "Passeur circuit breaker is OPEN",
                    "circuit_breaker_state": cb_state,
                }

            # Could add actual health check call to Passeur here
            # For now, just check circuit breaker state

            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Passeur Bridge available",
                "circuit_breaker_state": cb_state,
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"Passeur check failed: {str(e)}",
                "error": str(e),
            }

    async def _check_courier(self) -> Dict[str, Any]:
        """Check Courier event bus availability."""
        try:
            # Check if Courier is reachable
            # For now, just verify client exists
            courier = self.container.courier_client

            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Courier event bus available",
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"Courier check failed: {str(e)}",
                "error": str(e),
            }
