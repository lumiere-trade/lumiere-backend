"""
Courier Health Checker implementation.

Implements HealthChecker protocol from shared.health.
"""

import time
from datetime import datetime
from typing import Optional

from shared.health import HealthCheck, HealthChecker, HealthReport, HealthStatus

from courier.config.settings import Settings
from courier.infrastructure.websocket import ConnectionManager


class CourierHealthChecker(HealthChecker):
    """
    Health checker for Courier event bus.

    Checks:
    - Service liveness (basic check)
    - WebSocket connection capacity
    - Connection manager operational status
    """

    def __init__(
        self,
        settings: Settings,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        """
        Initialize health checker.

        Args:
            settings: Courier settings
            connection_manager: Optional ConnectionManager for readiness checks
        """
        self.settings = settings
        self.connection_manager = connection_manager

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
                name="courier",
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

        Checks connection capacity and manager availability.
        Used by Kubernetes to route traffic.

        Returns:
            HealthReport with readiness status
        """
        checks = {}
        overall_status = HealthStatus.HEALTHY

        # Check WebSocket connection capacity
        if self.connection_manager:
            capacity_check = self._check_connection_capacity()
            checks["connection_capacity"] = capacity_check
            if capacity_check.status != HealthStatus.HEALTHY:
                overall_status = capacity_check.status

            # Check connection manager operational
            manager_check = self._check_connection_manager()
            checks["connection_manager"] = manager_check
            if manager_check.status != HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        else:
            # No connection manager - service not ready
            checks["connection_manager"] = HealthCheck(
                name="connection_manager",
                status=HealthStatus.UNHEALTHY,
                message="Connection manager not initialized",
                timestamp=datetime.utcnow(),
            )
            overall_status = HealthStatus.UNHEALTHY

        return HealthReport(
            status=overall_status,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    def _check_connection_capacity(self) -> HealthCheck:
        """Check if WebSocket connection capacity is available."""
        start = time.time()

        try:
            total_connections = self.connection_manager.get_total_connections()
            max_connections = self.settings.max_total_connections

            duration = time.time() - start

            # Metadata for machine consumption
            metadata = {
                "total_connections": total_connections,
                "max_connections": (
                    max_connections if max_connections > 0 else None
                ),
            }

            # No limit configured - always healthy
            if max_connections <= 0:
                return HealthCheck(
                    name="connection_capacity",
                    status=HealthStatus.HEALTHY,
                    message=f"Unlimited capacity ({total_connections} active)",
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    metadata=metadata,
                )

            # Calculate capacity percentage
            capacity_pct = (total_connections / max_connections) * 100
            metadata["capacity_percent"] = round(capacity_pct, 1)

            # Degraded if over 90% capacity
            if capacity_pct >= 90:
                return HealthCheck(
                    name="connection_capacity",
                    status=HealthStatus.DEGRADED,
                    message=(
                        f"High capacity usage: {total_connections}/"
                        f"{max_connections} ({capacity_pct:.1f}%)"
                    ),
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    metadata=metadata,
                )

            # Healthy
            return HealthCheck(
                name="connection_capacity",
                status=HealthStatus.HEALTHY,
                message=(
                    f"Capacity available: {total_connections}/"
                    f"{max_connections} ({capacity_pct:.1f}%)"
                ),
                duration=duration,
                timestamp=datetime.utcnow(),
                metadata=metadata,
            )

        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="connection_capacity",
                status=HealthStatus.UNHEALTHY,
                message=f"Capacity check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )

    def _check_connection_manager(self) -> HealthCheck:
        """Check if connection manager is operational."""
        start = time.time()

        try:
            # Simple operational check
            channels = self.connection_manager.get_all_channels()
            duration = time.time() - start

            metadata = {
                "active_channels": len(channels),
                "channel_names": list(channels.keys()),
            }

            return HealthCheck(
                name="connection_manager",
                status=HealthStatus.HEALTHY,
                message=f"Operational ({len(channels)} active channels)",
                duration=duration,
                timestamp=datetime.utcnow(),
                metadata=metadata,
            )

        except Exception as e:
            duration = time.time() - start
            return HealthCheck(
                name="connection_manager",
                status=HealthStatus.UNHEALTHY,
                message=f"Manager check failed: {str(e)}",
                duration=duration,
                timestamp=datetime.utcnow(),
            )
