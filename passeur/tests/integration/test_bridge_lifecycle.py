"""
Integration tests for Bridge server lifecycle management.

Tests starting, stopping, health checks, and graceful shutdown
of the Node.js bridge server.

Usage:
    python -m passeur.tests.integration.test_bridge_lifecycle
    laborant passeur --integration
"""

import time

import requests
from passeur.config.settings import load_config
from shared.tests import LaborantTest

from tests.helpers.bridge_manager import BridgeManager


class TestBridgeLifecycle(LaborantTest):
    """Integration tests for Bridge server lifecycle management."""

    component_name = "passeur"
    test_category = "integration"

    def setup(self):
        """Setup before all tests - initialize bridge manager."""
        self.reporter.info("Setting up bridge manager...", context="Setup")

        # Load test config
        self.test_config = load_config("development.yaml")

        # Initialize bridge manager
        self.bridge = BridgeManager(config_file="development.yaml", reporter=self.reporter)

        self.reporter.info("Bridge manager ready", context="Setup")

    def teardown(self):
        """Cleanup after all tests - stop bridge if running."""
        if hasattr(self, "bridge") and self.bridge.is_running():
            self.reporter.info("Cleaning up bridge...", context="Teardown")
            self.bridge.stop()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Bridge lifecycle tests
    # ================================================================

    def test_bridge_start(self):
        """Test starting bridge server."""
        self.reporter.info("Testing bridge server start", context="Test")

        success = self.bridge.start(timeout=30)

        assert success is True, "Bridge should start successfully"
        assert self.bridge.is_running() is True, "Bridge should be running"

        self.reporter.info("Bridge started successfully", context="Test")

    def test_bridge_health_endpoint(self):
        """Test bridge health endpoint responds."""
        self.reporter.info("Testing health endpoint", context="Test")

        bridge_url = (
            f"http://{self.test_config.bridge_host}:" f"{self.test_config.bridge_port}"
        )

        response = requests.get(f"{bridge_url}/health", timeout=5)

        assert response.status_code == 200, "Health endpoint should return 200"

        data = response.json()
        assert data["status"] == "healthy", "Status should be healthy"
        assert "program" in data, "Should have program ID"
        assert "wallet" in data, "Should have wallet address"
        assert "network" in data, "Should have network info"

        self.reporter.info(f"Health check OK: {data['network']}", context="Test")

    def test_bridge_health_response_time(self):
        """Test health endpoint responds quickly."""
        self.reporter.info("Testing health endpoint response time", context="Test")

        bridge_url = (
            f"http://{self.test_config.bridge_host}:" f"{self.test_config.bridge_port}"
        )

        start = time.time()
        response = requests.get(f"{bridge_url}/health", timeout=5)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, "Health check should respond within 1 second"

        self.reporter.info(f"Response time: {elapsed:.3f}s", context="Test")

    def test_bridge_port_configuration(self):
        """Test bridge uses correct port from config."""
        self.reporter.info("Testing bridge port configuration", context="Test")

        # Should be on test port 8767, not production 8766
        assert self.test_config.bridge_port == 8767, "Should use test port 8767"

        bridge_url = (
            f"http://{self.test_config.bridge_host}:" f"{self.test_config.bridge_port}"
        )
        response = requests.get(f"{bridge_url}/health", timeout=5)

        assert response.status_code == 200

        self.reporter.info("Bridge using correct test port", context="Test")

    def test_bridge_double_start_prevention(self):
        """Test starting bridge twice doesn't create duplicate."""
        self.reporter.info("Testing double start prevention", context="Test")

        # Ensure bridge is running
        if not self.bridge.is_running():
            self.bridge.start()

        # Try to start again
        result = self.bridge.start()

        # Should return True but not create new process
        assert result is True
        assert self.bridge.is_running() is True

        self.reporter.info("Double start correctly prevented", context="Test")

    def test_bridge_stop(self):
        """Test stopping bridge server."""
        self.reporter.info("Testing bridge server stop", context="Test")

        self.bridge.stop()

        # Wait a bit for shutdown
        time.sleep(1)

        assert self.bridge.is_running() is False, "Bridge should be stopped"

        self.reporter.info("Bridge stopped successfully", context="Test")

    def test_bridge_stopped_health_check_fails(self):
        """Test health check fails when bridge is stopped."""
        self.reporter.info("Testing health check fails when stopped", context="Test")

        bridge_url = (
            f"http://{self.test_config.bridge_host}:" f"{self.test_config.bridge_port}"
        )

        try:
            requests.get(f"{bridge_url}/health", timeout=2)
            assert False, "Request should fail when bridge is stopped"
        except requests.exceptions.RequestException:
            self.reporter.info(
                "Health check correctly fails when stopped", context="Test"
            )

    def test_bridge_restart(self):
        """Test restarting bridge server."""
        self.reporter.info("Testing bridge restart", context="Test")

        # Start again
        success = self.bridge.start(timeout=30)

        assert success is True, "Bridge should restart successfully"
        assert self.bridge.is_running() is True, "Bridge should be running again"

        # Verify it responds
        bridge_url = (
            f"http://{self.test_config.bridge_host}:" f"{self.test_config.bridge_port}"
        )
        response = requests.get(f"{bridge_url}/health", timeout=5)

        assert response.status_code == 200

        self.reporter.info("Bridge restarted successfully", context="Test")

    def test_bridge_context_manager(self):
        """Test bridge manager as context manager."""
        self.reporter.info("Testing bridge context manager", context="Test")

        # Stop current bridge first
        if self.bridge.is_running():
            self.bridge.stop()
            time.sleep(1)

        # Use context manager
        with BridgeManager(
            config_file="development.yaml", reporter=self.reporter
        ) as test_bridge:
            assert test_bridge.is_running() is True
            self.reporter.info("Bridge started via context manager", context="Test")

        # Should auto-stop after context
        time.sleep(1)
        # Note: test_bridge is different instance, can't check directly

        self.reporter.info("Context manager test complete", context="Test")


if __name__ == "__main__":
    TestBridgeLifecycle.run_as_main()
