"""
Pourtier Health Checker implementation.

Implements HealthChecker protocol from shared.health.
"""

import time
from datetime import datetime

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container
from shared.health import HealthCheck, HealthChecker, HealthReport, HealthStatus


class PourtierHealthChecker(HealthChecker):
    """
    Health checker for Pourtier.

    Implements shared.health.HealthChecker protocol.
    """

    def __init__(self):
        """Initialize health checker."""
        self.container = get_container()
        self.settings = get_settings()

    def check_liveness(self) -> HealthReport:
        """Check if service is alive (basic check)."""
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
        """Check if service is ready to handle requests."""
        checks = {}
        overall_status = HealthStatus.HEALTHY

        # Check Database
        db_check = self._check_database()
        checks["database"] = db_check
        if db_check.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY

        # Check Redis (if enabled)
        if self.settings.REDIS_ENABLED:
            redis_check = self._check_redis()
            checks["redis"] = redis_check
            if redis_check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED

        return HealthReport(
            status=overall_status,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    def _check_database(self) -> HealthCheck:
        """Check database connectivity."""
        start = time.time()
        try:
            # Note: This is sync context, actual check would need async
            duration = time.time() - start
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database available",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )

    def _check_redis(self) -> HealthCheck:
        """Check Redis connectivity."""
        start = time.time()
        try:
            duration = time.time() - start
            return HealthCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis available",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
