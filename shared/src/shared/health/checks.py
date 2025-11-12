"""
Health check definitions and status types.

Defines health check interface and status enums.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Protocol


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """
    Health check result.

    Represents the result of a single health check operation.
    """

    name: str
    status: HealthStatus
    message: Optional[str] = None
    duration: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "name": self.name,
            "status": self.status.value,
        }

        if self.message:
            result["message"] = self.message

        if self.duration is not None:
            result["duration"] = self.duration

        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()

        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class HealthReport:
    """
    Overall health report.

    Aggregates multiple health checks into overall status.
    """

    status: HealthStatus
    checks: Dict[str, HealthCheck]
    version: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON response.

        Returns:
            Dictionary representation
        """
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "duration": check.duration,
                    **({"metadata": check.metadata} if check.metadata else {}),
                }
                for name, check in self.checks.items()
            },
        }

    @property
    def is_healthy(self) -> bool:
        """Check if overall status is healthy."""
        return self.status == HealthStatus.HEALTHY

    @property
    def is_ready(self) -> bool:
        """Check if service is ready (healthy or degraded)."""
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


class HealthChecker(Protocol):
    """
    Protocol for health checker implementations.

    Each service should implement this protocol with service-specific checks.
    """

    def check_liveness(self) -> HealthReport:
        """
        Perform liveness check.

        Liveness checks if service is alive and functioning.
        Failure indicates service needs restart.

        Returns:
            HealthReport with liveness status
        """
        ...

    def check_readiness(self) -> HealthReport:
        """
        Perform readiness check.

        Readiness checks if service can handle requests.
        Failure indicates service should not receive traffic.

        Returns:
            HealthReport with readiness status
        """
        ...
