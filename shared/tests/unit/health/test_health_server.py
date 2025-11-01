"""
Unit tests for HealthServer.

Tests HTTP server functionality and endpoints.

Usage:
    python -m tests.unit.infrastructure.health.test_health_server
"""

import time
from threading import Thread
from unittest.mock import Mock

import requests

from shared.health import HealthChecker, HealthServer
from shared.tests import LaborantTest


class TestHealthServer(LaborantTest):
    """Test health server HTTP endpoints."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""
        self.base_port = 8100
        self.test_host = "127.0.0.1"

    def teardown(self):
        """Cleanup after tests."""
        time.sleep(0.2)

    def _start_server_background(self, server: HealthServer) -> Thread:
        """Start server in background thread."""
        server_thread = Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(1.0)  # Increased wait time
        return server_thread

    def _stop_server(self, server: HealthServer, thread: Thread) -> None:
        """Stop server and wait for thread."""
        server.shutdown()
        thread.join(timeout=2)
        time.sleep(0.2)

    def test_server_initialization(self):
        """Test server can be initialized."""
        checker = HealthChecker()
        server = HealthServer(
            host=self.test_host, port=self.base_port, health_checker=checker
        )

        assert server.host == self.test_host
        assert server.port == self.base_port
        assert server.health_checker is not None

    def test_server_starts_successfully(self):
        """Test server starts and binds to port."""
        port = self.base_port + 1
        checker = HealthChecker()
        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        assert server.httpd is not None

        self._stop_server(server, thread)

    def test_health_endpoint_accessible(self):
        """Test /health endpoint returns 200 OK."""
        port = self.base_port + 2

        # Mock checker to avoid smoke test
        checker = Mock()
        mock_report = Mock()
        mock_report.is_ready = True
        mock_report.to_dict = Mock(
            return_value={
                "status": "healthy",
                "checks": {},
                "version": "2.0.0",
                "timestamp": "2025-10-31T15:00:00Z",
            }
        )
        checker.check_readiness = Mock(return_value=mock_report)

        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        try:
            response = requests.get(f"http://{self.test_host}:{port}/health", timeout=5)
            assert response.status_code == 200
        finally:
            self._stop_server(server, thread)

    def test_health_endpoint_returns_json(self):
        """Test /health endpoint returns JSON."""
        port = self.base_port + 3

        # Mock checker
        checker = Mock()
        mock_report = Mock()
        mock_report.is_ready = True
        mock_report.to_dict = Mock(
            return_value={
                "status": "healthy",
                "checks": {},
                "version": "2.0.0",
                "timestamp": "2025-10-31T15:00:00Z",
            }
        )
        checker.check_readiness = Mock(return_value=mock_report)

        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        try:
            response = requests.get(f"http://{self.test_host}:{port}/health", timeout=5)
            data = response.json()

            assert "status" in data
            assert "version" in data
        finally:
            self._stop_server(server, thread)

    def test_liveness_endpoint_accessible(self):
        """Test /health/live endpoint returns 200 OK."""
        port = self.base_port + 4

        # Mock checker
        checker = Mock()
        mock_report = Mock()
        mock_report.is_healthy = True
        mock_report.to_dict = Mock(
            return_value={
                "status": "healthy",
                "checks": {},
                "version": "2.0.0",
                "timestamp": "2025-10-31T15:00:00Z",
            }
        )
        checker.check_liveness = Mock(return_value=mock_report)

        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        try:
            response = requests.get(
                f"http://{self.test_host}:{port}/health/live", timeout=5
            )
            assert response.status_code == 200
        finally:
            self._stop_server(server, thread)

    def test_readiness_endpoint_accessible(self):
        """Test /health/ready endpoint returns 200 OK."""
        port = self.base_port + 5

        # Mock checker to avoid smoke test
        checker = Mock()
        mock_report = Mock()
        mock_report.is_ready = True
        mock_report.to_dict = Mock(
            return_value={
                "status": "healthy",
                "checks": {},
                "version": "2.0.0",
                "timestamp": "2025-10-31T15:00:00Z",
            }
        )
        checker.check_readiness = Mock(return_value=mock_report)

        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        try:
            response = requests.get(
                f"http://{self.test_host}:{port}/health/ready", timeout=5
            )
            assert response.status_code == 200
        finally:
            self._stop_server(server, thread)

    def test_invalid_endpoint_returns_404(self):
        """Test invalid endpoint returns 404."""
        port = self.base_port + 6

        # Mock checker
        checker = Mock()

        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        try:
            response = requests.get(
                f"http://{self.test_host}:{port}/invalid", timeout=5
            )
            assert response.status_code == 404
        finally:
            self._stop_server(server, thread)

    def test_graceful_shutdown(self):
        """Test server stops cleanly."""
        port = self.base_port + 7
        checker = Mock()
        server = HealthServer(host=self.test_host, port=port, health_checker=checker)

        thread = self._start_server_background(server)

        assert server.httpd is not None

        self._stop_server(server, thread)

        assert server.httpd is None


if __name__ == "__main__":
    TestHealthServer.run_as_main()
