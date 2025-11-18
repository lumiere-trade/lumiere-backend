"""
Pourtier Health Checker implementation.

Implements HealthChecker protocol from shared.health.
"""

import time
from datetime import datetime

from shared.health import HealthCheck, HealthChecker, HealthReport, HealthStatus

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container


class PourtierHealthChecker(HealthChecker):
    """
    Health checker for Pourtier.

    Implements shared.health.HealthChecker protocol.
    Checks database engine initialization and Redis (if enabled).
    """

    def __init__(self):
        """Initialize health checker."""
        self.container = get_container()
        self.settings = get_settings()

    def check_liveness(self) -> HealthReport:
        """
        Check if service is alive (basic check).

        Returns basic service info without checking dependencies.

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
        Check if service is ready to handle requests.

        Checks critical dependencies (database) and optional (Redis).

        Returns:
            HealthReport with readiness status
        """
        checks = {}
        overall_status = HealthStatus.HEALTHY

        # Check Database (CRITICAL)
        db_check = self._check_database()
        checks["database"] = db_check

        if db_check.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY

        # Check Redis (OPTIONAL - if enabled)
        if self.settings.REDIS_ENABLED:
            redis_check = self._check_redis()
            checks["redis"] = redis_check
            # Redis failure = DEGRADED (not UNHEALTHY)
            if redis_check.status == HealthStatus.UNHEALTHY:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        return HealthReport(
            status=overall_status,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    def _check_database(self) -> HealthCheck:
        """
        Check database engine initialization.

        Note: This is a sync context check. Engine existence indicates
        successful initialization. Pool connections are created lazily.

        Returns:
            HealthCheck with database status
        """
        start = time.time()
        try:
            # Check if database engine is initialized
            db_healthy = (
                hasattr(self.container.database, "_engine")
                and self.container.database._engine is not None
            )

            duration = time.time() - start

            if db_healthy:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database available",
                    duration=duration,
                    timestamp=datetime.utcnow(),
                )
            else:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database not initialized",
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
        """
        Check Redis connectivity.

        Note: This is a sync context check. Client existence indicates
        successful initialization. Actual connection is tested with ping.

        Returns:
            HealthCheck with Redis status
        """
        start = time.time()
        try:
            # Check if Redis client is initialized
            redis_healthy = (
                hasattr(self.container.cache_client, "_client")
                and self.container.cache_client._client is not None
            )

            duration = time.time() - start

            if redis_healthy:
                return HealthCheck(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis available",
                    duration=duration,
                    timestamp=datetime.utcnow(),
                )
            else:
                return HealthCheck(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis not initialized",
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
