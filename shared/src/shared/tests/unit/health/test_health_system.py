"""
Unit tests for Health Check System.

Tests health check protocol, data models, and server initialization.

Usage:
    python tests/unit/health/test_health_system.py
    laborant test shared --unit
"""

from datetime import datetime

from shared.health import (
    HealthCheck,
    HealthReport,
    HealthServer,
    HealthStatus,
)
from shared.tests import LaborantTest


class SimpleHealthChecker:
    """Simple health checker implementation for testing."""

    def __init__(self, version: str = "test-1.0.0"):
        self.version = version
        self.healthy = True

    def check_liveness(self) -> HealthReport:
        """Simple liveness check."""
        checks = {
            "service": HealthCheck(
                name="service",
                status=HealthStatus.HEALTHY,
                message="Service is running",
                timestamp=datetime.utcnow(),
            )
        }

        return HealthReport(
            status=HealthStatus.HEALTHY,
            checks=checks,
            version=self.version,
            timestamp=datetime.utcnow(),
        )

    def check_readiness(self) -> HealthReport:
        """Simple readiness check."""
        status = HealthStatus.HEALTHY if self.healthy else HealthStatus.UNHEALTHY

        checks = {
            "service": HealthCheck(
                name="service",
                status=status,
                message=("Service ready" if self.healthy else "Service not ready"),
                timestamp=datetime.utcnow(),
            )
        }

        return HealthReport(
            status=status,
            checks=checks,
            version=self.version,
            timestamp=datetime.utcnow(),
        )


class TestHealthSystem(LaborantTest):
    """Unit tests for Health Check System."""

    component_name = "shared"
    test_category = "unit"

    # ================================================================
    # HealthStatus tests
    # ================================================================

    def test_health_status_enum_values(self):
        """Test HealthStatus enum has correct values."""
        self.reporter.info("Testing HealthStatus enum values", context="Test")

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

        self.reporter.info("HealthStatus enum values correct", context="Test")

    # ================================================================
    # HealthCheck tests
    # ================================================================

    def test_health_check_creation(self):
        """Test HealthCheck creation with required fields."""
        self.reporter.info("Testing HealthCheck creation", context="Test")

        check = HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connected",
            duration=0.05,
            timestamp=datetime.utcnow(),
        )

        assert check.name == "database"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "Database connected"
        assert check.duration == 0.05
        assert isinstance(check.timestamp, datetime)

        self.reporter.info("HealthCheck created successfully", context="Test")

    def test_health_check_to_dict(self):
        """Test HealthCheck.to_dict() serialization."""
        self.reporter.info(
            "Testing HealthCheck.to_dict() serialization", context="Test"
        )

        timestamp = datetime.utcnow()
        check = HealthCheck(
            name="redis",
            status=HealthStatus.DEGRADED,
            message="Redis slow",
            duration=1.5,
            timestamp=timestamp,
        )

        result = check.to_dict()

        assert result["name"] == "redis"
        assert result["status"] == "degraded"
        assert result["message"] == "Redis slow"
        assert result["duration"] == 1.5
        assert result["timestamp"] == timestamp.isoformat()

        self.reporter.info("HealthCheck serialized correctly", context="Test")

    def test_health_check_minimal_fields(self):
        """Test HealthCheck with only required fields."""
        self.reporter.info("Testing HealthCheck with minimal fields", context="Test")

        check = HealthCheck(name="service", status=HealthStatus.HEALTHY)

        assert check.name == "service"
        assert check.status == HealthStatus.HEALTHY
        assert check.message is None
        assert check.duration is None
        assert check.timestamp is None

        self.reporter.info("Minimal HealthCheck created", context="Test")

    # ================================================================
    # HealthReport tests
    # ================================================================

    def test_health_report_creation(self):
        """Test HealthReport creation with checks."""
        self.reporter.info("Testing HealthReport creation", context="Test")

        checks = {
            "db": HealthCheck(name="db", status=HealthStatus.HEALTHY, message="DB OK"),
            "cache": HealthCheck(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="Cache OK",
            ),
        }

        report = HealthReport(
            status=HealthStatus.HEALTHY,
            checks=checks,
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        assert report.status == HealthStatus.HEALTHY
        assert len(report.checks) == 2
        assert "db" in report.checks
        assert "cache" in report.checks
        assert report.version == "1.0.0"

        self.reporter.info("HealthReport created successfully", context="Test")

    def test_health_report_is_healthy_property(self):
        """Test HealthReport.is_healthy property."""
        self.reporter.info("Testing HealthReport.is_healthy property", context="Test")

        healthy_report = HealthReport(
            status=HealthStatus.HEALTHY,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        degraded_report = HealthReport(
            status=HealthStatus.DEGRADED,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        unhealthy_report = HealthReport(
            status=HealthStatus.UNHEALTHY,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        assert healthy_report.is_healthy is True
        assert degraded_report.is_healthy is False
        assert unhealthy_report.is_healthy is False

        self.reporter.info("is_healthy property working correctly", context="Test")

    def test_health_report_is_ready_property(self):
        """Test HealthReport.is_ready property."""
        self.reporter.info("Testing HealthReport.is_ready property", context="Test")

        healthy_report = HealthReport(
            status=HealthStatus.HEALTHY,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        degraded_report = HealthReport(
            status=HealthStatus.DEGRADED,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        unhealthy_report = HealthReport(
            status=HealthStatus.UNHEALTHY,
            checks={},
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        assert healthy_report.is_ready is True
        assert degraded_report.is_ready is True
        assert unhealthy_report.is_ready is False

        self.reporter.info("is_ready property working correctly", context="Test")

    def test_health_report_to_dict(self):
        """Test HealthReport.to_dict() serialization."""
        self.reporter.info(
            "Testing HealthReport.to_dict() serialization", context="Test"
        )

        checks = {
            "service": HealthCheck(
                name="service",
                status=HealthStatus.HEALTHY,
                message="Running",
                duration=0.01,
            )
        }

        report = HealthReport(
            status=HealthStatus.HEALTHY,
            checks=checks,
            version="2.0.0",
            timestamp=datetime.utcnow(),
        )

        result = report.to_dict()

        assert result["status"] == "healthy"
        assert result["version"] == "2.0.0"
        assert "timestamp" in result
        assert "checks" in result
        assert "service" in result["checks"]
        assert result["checks"]["service"]["status"] == "healthy"

        self.reporter.info("HealthReport serialized correctly", context="Test")

    # ================================================================
    # HealthChecker Protocol tests
    # ================================================================

    def test_simple_health_checker_implements_protocol(self):
        """Test SimpleHealthChecker implements HealthChecker protocol."""
        self.reporter.info(
            "Testing SimpleHealthChecker protocol implementation",
            context="Test",
        )

        checker = SimpleHealthChecker()

        assert hasattr(checker, "check_liveness")
        assert hasattr(checker, "check_readiness")
        assert callable(checker.check_liveness)
        assert callable(checker.check_readiness)

        self.reporter.info("Protocol implemented correctly", context="Test")

    def test_health_checker_liveness(self):
        """Test HealthChecker.check_liveness() returns HealthReport."""
        self.reporter.info("Testing HealthChecker.check_liveness()", context="Test")

        checker = SimpleHealthChecker(version="1.2.3")
        report = checker.check_liveness()

        assert isinstance(report, HealthReport)
        assert report.status == HealthStatus.HEALTHY
        assert report.version == "1.2.3"
        assert "service" in report.checks
        assert report.is_healthy is True

        self.reporter.info("Liveness check working correctly", context="Test")

    def test_health_checker_readiness_healthy(self):
        """Test HealthChecker.check_readiness() when healthy."""
        self.reporter.info(
            "Testing HealthChecker.check_readiness() - healthy", context="Test"
        )

        checker = SimpleHealthChecker()
        checker.healthy = True

        report = checker.check_readiness()

        assert isinstance(report, HealthReport)
        assert report.status == HealthStatus.HEALTHY
        assert report.is_ready is True

        self.reporter.info("Readiness check returns healthy status", context="Test")

    def test_health_checker_readiness_unhealthy(self):
        """Test HealthChecker.check_readiness() when unhealthy."""
        self.reporter.info(
            "Testing HealthChecker.check_readiness() - unhealthy",
            context="Test",
        )

        checker = SimpleHealthChecker()
        checker.healthy = False

        report = checker.check_readiness()

        assert isinstance(report, HealthReport)
        assert report.status == HealthStatus.UNHEALTHY
        assert report.is_ready is False
        assert report.is_healthy is False

        self.reporter.info("Readiness check returns unhealthy status", context="Test")

    # ================================================================
    # HealthServer tests
    # ================================================================

    def test_health_server_initialization(self):
        """Test HealthServer initialization with checker."""
        self.reporter.info("Testing HealthServer initialization", context="Test")

        checker = SimpleHealthChecker()
        server = HealthServer(checker, host="127.0.0.1", port=8888)

        assert server.health_checker == checker
        assert server.host == "127.0.0.1"
        assert server.port == 8888
        assert server.server is None

        self.reporter.info("HealthServer initialized correctly", context="Test")

    def test_health_server_default_host_port(self):
        """Test HealthServer uses default host and port."""
        self.reporter.info("Testing HealthServer default values", context="Test")

        checker = SimpleHealthChecker()
        server = HealthServer(checker)

        assert server.host == "0.0.0.0"
        assert server.port == 8080

        self.reporter.info("Default host and port correct", context="Test")


if __name__ == "__main__":
    TestHealthSystem.run_as_main()
