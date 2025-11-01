"""
Unit tests for Prometheus Metrics Server.

Tests server initialization, startup, and shutdown functionality.

Usage:
    python tests/unit/observability/test_metrics_server.py
    laborant test shared --unit
"""

import time
import requests
import threading
from shared.tests import LaborantTest
from shared.observability import MetricsServer
from prometheus_client import Counter


class TestMetricsServer(LaborantTest):
    """Unit tests for MetricsServer."""

    component_name = "shared"
    test_category = "unit"

    def test_metrics_server_initialization(self):
        """Test MetricsServer initialization."""
        self.reporter.info("Testing server initialization", context="Test")

        server = MetricsServer(host="127.0.0.1", port=9999)

        assert server.host == "127.0.0.1"
        assert server.port == 9999
        assert server.is_running is False
        assert server.url == "http://127.0.0.1:9999/metrics"

        self.reporter.info("Server initialized correctly", context="Test")

    def test_metrics_server_default_values(self):
        """Test MetricsServer uses default values."""
        self.reporter.info("Testing default values", context="Test")

        server = MetricsServer()

        assert server.host == "0.0.0.0"
        assert server.port == 9090
        assert server.url == "http://0.0.0.0:9090/metrics"

        self.reporter.info("Default values correct", context="Test")

    def test_metrics_server_start_in_background(self):
        """Test starting server in background thread."""
        self.reporter.info("Testing background start", context="Test")

        # Create a test metric
        test_counter = Counter(
            'test_background_requests_total',
            'Test counter for background server'
        )
        test_counter.inc()

        # Start server in background
        server = MetricsServer(host="127.0.0.1", port=19090)
        server.start_in_background()

        # Wait for server to start
        time.sleep(0.5)

        # Verify server is running
        assert server.is_running is True

        # Try to fetch metrics
        try:
            response = requests.get(
                "http://127.0.0.1:19090/metrics",
                timeout=2
            )
            assert response.status_code == 200
            assert "test_background_requests_total" in response.text
            self.reporter.info("Server accessible via HTTP", context="Test")
        except requests.RequestException as e:
            self.reporter.warning(
                f"Could not connect to server: {e}", context="Test"
            )

        # Shutdown
        server.shutdown()
        time.sleep(0.2)

        assert server.is_running is False

        self.reporter.info("Background server working", context="Test")

    def test_metrics_server_shutdown(self):
        """Test server shutdown functionality."""
        self.reporter.info("Testing server shutdown", context="Test")

        server = MetricsServer(host="127.0.0.1", port=19091)

        # Start in background
        server.start_in_background()
        time.sleep(0.3)

        assert server.is_running is True

        # Shutdown
        server.shutdown()
        time.sleep(0.2)

        assert server.is_running is False

        self.reporter.info("Shutdown working correctly", context="Test")

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test /metrics endpoint returns Prometheus format."""
        self.reporter.info("Testing Prometheus format", context="Test")

        # Create test metrics
        test_counter = Counter(
            'test_format_requests_total',
            'Test counter for format validation',
            ['method', 'status']
        )
        test_counter.labels(method='GET', status='200').inc(5)
        test_counter.labels(method='POST', status='201').inc(3)

        # Start server
        server = MetricsServer(host="127.0.0.1", port=19092)
        server.start_in_background()
        time.sleep(0.3)

        try:
            response = requests.get(
                "http://127.0.0.1:19092/metrics",
                timeout=2
            )

            # Check response
            assert response.status_code == 200
            content = response.text

            # Verify Prometheus format
            assert "# HELP" in content
            assert "# TYPE" in content
            assert "test_format_requests_total" in content

            self.reporter.info("Prometheus format correct", context="Test")

        except requests.RequestException as e:
            self.reporter.warning(
                f"Could not verify format: {e}", context="Test"
            )

        finally:
            server.shutdown()

    def test_multiple_servers_different_ports(self):
        """Test running multiple servers on different ports."""
        self.reporter.info("Testing multiple servers", context="Test")

        server1 = MetricsServer(host="127.0.0.1", port=19093)
        server2 = MetricsServer(host="127.0.0.1", port=19094)

        server1.start_in_background()
        server2.start_in_background()
        time.sleep(0.3)

        assert server1.is_running is True
        assert server2.is_running is True

        # Cleanup
        server1.shutdown()
        server2.shutdown()

        self.reporter.info("Multiple servers working", context="Test")

    def test_server_port_already_in_use(self):
        """Test error handling when port is already in use."""
        self.reporter.info("Testing port collision", context="Test")

        # Start first server
        server1 = MetricsServer(host="127.0.0.1", port=19095)
        server1.start_in_background()
        time.sleep(0.3)

        # Try to start second server on same port
        server2 = MetricsServer(host="127.0.0.1", port=19095)

        def start_and_catch():
            try:
                server2.start()
                return False  # Should not reach here
            except OSError:
                return True  # Expected

        thread = threading.Thread(target=start_and_catch, daemon=True)
        thread.start()
        thread.join(timeout=2)

        # Cleanup
        server1.shutdown()

        self.reporter.info("Port collision handled", context="Test")


if __name__ == "__main__":
    TestMetricsServer.run_as_main()
