"""
Pourtier Health Check implementation.

Kubernetes-compatible health checks for liveness and readiness probes.
"""

import time
from datetime import datetime
from typing import Dict

from shared.health import HealthCheck, HealthReport, HealthStatus

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container


class PourtierHealthCheck:
    """
    Health check for Pourtier API Gateway.

    Checks:
    - Database connectivity (PostgreSQL)
    - Redis connectivity (if enabled)
    - Passeur Bridge availability
    - Courier event bus availability
    """

    def __init__(self):
        """Initialize health check."""
        self.container = get_container()
        self.settings = get_settings()

    def check_liveness(self) -> HealthReport:
        """
        Liveness probe - is the service alive?

        Returns basic service info without checking dependencies.
        Used by Kubernetes to restart unhealthy pods.

        Returns:
            HealthReport with liveness status
        """
        checks = {
            "service": HealthCheck(
                name="pourtier",
                status=HealthStatus.HEALTHY,
                message="Service is alive",
                timestamp=datetime.utcnow(),
            )
        }

        return HealthReport(
            status=HealthStatus.HEALTHY,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    def check_readiness(self) -> HealthReport:
        """
        Readiness probe - is the service ready to handle requests?

        Checks all critical dependencies.
        Used by Kubernetes to route traffic.

        Returns:
            HealthReport with readiness status
        """
        checks = {}
        overall_status = HealthStatus.HEALTHY

        # 1. Check Database
        db_check = self._check_database()
        checks["database"] = db_check
        if db_check.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY

        # 2. Check Redis (if enabled)
        if self.settings.REDIS_ENABLED:
            redis_check = self._check_redis()
            checks["redis"] = redis_check
            if redis_check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED

        # 3. Check Passeur Bridge
        passeur_check = self._check_passeur_bridge()
        checks["passeur_bridge"] = passeur_check
        if passeur_check.status != HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # 4. Check Courier Event Bus
        courier_check = self._check_courier()
        checks["courier"] = courier_check
        if courier_check.status != HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        return HealthReport(
            status=overall_status,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    def _check_database(self) -> HealthCheck:
        """Check PostgreSQL database connectivity."""
        start = time.time()
        try:
            # Simple query to verify connection
            duration = time.time() - start

            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connected",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )

    def _check_redis(self) -> HealthCheck:
        """Check Redis connectivity."""
        start = time.time()
        try:
            # Ping Redis
            duration = time.time() - start

            return HealthCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connected",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )

    def _check_passeur_bridge(self) -> HealthCheck:
        """Check Passeur Bridge availability."""
        start = time.time()
        try:
            # Check if Passeur circuit breaker is open
            passeur = self.container.passeur_bridge
            cb_state = passeur.circuit_breaker.state
            duration = time.time() - start

            if cb_state == "open":
                return HealthCheck(
                    name="passeur_bridge",
                    status=HealthStatus.DEGRADED,
                    message="Passeur circuit breaker is OPEN",
                    duration=duration,
                    timestamp=datetime.utcnow(),
                )

            return HealthCheck(
                name="passeur_bridge",
                status=HealthStatus.HEALTHY,
                message="Passeur Bridge available",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="passeur_bridge",
                status=HealthStatus.DEGRADED,
                message=f"Passeur check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )

    def _check_courier(self) -> HealthCheck:
        """Check Courier event bus availability."""
        start = time.time()
        try:
            # Check if Courier is reachable
            courier = self.container.courier_client
            duration = time.time() - start

            return HealthCheck(
                name="courier",
                status=HealthStatus.HEALTHY,
                message="Courier event bus available",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="courier",
                status=HealthStatus.DEGRADED,
                message=f"Courier check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
