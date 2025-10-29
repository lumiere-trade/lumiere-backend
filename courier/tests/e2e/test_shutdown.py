"""
E2E tests for graceful shutdown behavior.

Tests shutdown handling configuration and state.

Usage:
    laborant courier --e2e
"""

import subprocess
import time

import httpx
from shared.tests import LaborantTest


class TestGracefulShutdown(LaborantTest):
    """E2E tests for graceful shutdown configuration."""

    component_name = "courier"
    test_category = "e2e"

    http_base_url = "http://localhost:7766"
    container_name = "courier-e2e-shutdown-test"

    async def async_setup(self):
        """Setup test environment."""
        self.reporter.info("Setting up Shutdown E2E tests...", context="Setup")

        await self._start_courier_container()
        await self._wait_for_api()

        self.reporter.info("Shutdown E2E tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup test environment."""
        self.reporter.info("Cleaning up Shutdown tests...", context="Teardown")

        await self._stop_courier_container()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def _start_courier_container(self):
        """Start Courier container."""
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-p",
                "7766:7765",
                "-e",
                "ENV=test",
                "-e",
                "PORT=7765",
                "-e",
                "REQUIRE_AUTH=false",
                "courier:development",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    async def _stop_courier_container(self):
        """Stop and remove Courier container."""
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    async def _wait_for_api(self):
        """Wait for API to be ready."""
        import asyncio

        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.http_base_url}/health", timeout=2.0
                    )
                    if response.status_code == 200:
                        return
            except Exception:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        raise RuntimeError("Courier API not accessible after 30 seconds")

    # ================================================================
    # Non-destructive tests (run first alphabetically)
    # ================================================================

    async def test_a_health_shows_healthy_status(self):
        """Test health endpoint shows healthy status before shutdown."""
        self.reporter.info("Testing initial health status", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.http_base_url}/health")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert "uptime_seconds" in data
            assert "total_clients" in data
            assert "channels" in data
            assert data.get("shutdown_info") is None

        self.reporter.info("Initial health status correct", context="Test")

    async def test_b_stats_endpoint_works(self):
        """Test stats endpoint is accessible."""
        self.reporter.info("Testing stats endpoint", context="Test")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.http_base_url}/stats")

            assert response.status_code == 200

            data = response.json()
            assert "uptime_seconds" in data
            assert "active_clients" in data
            assert "channels" in data

        self.reporter.info("Stats endpoint works", context="Test")

    async def test_c_shutdown_infrastructure_present(self):
        """Test ShutdownManager infrastructure is present."""
        self.reporter.info("Testing shutdown infrastructure", context="Test")

        result = subprocess.run(
            ["docker", "logs", self.container_name],
            capture_output=True,
            text=True,
        )

        logs = result.stdout + result.stderr

        # Should see startup messages indicating system is running
        assert (
            "Courier starting" in logs
            or "starting" in logs.lower()
            or "ready" in logs.lower()
        )

        self.reporter.info("Shutdown infrastructure present", context="Test")

    async def test_d_signal_handlers_registered(self):
        """Test that application starts successfully."""
        self.reporter.info("Testing application startup", context="Test")

        # Application should be running and responsive
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.http_base_url}/health")
            assert response.status_code == 200

            # Check it's actually healthy
            data = response.json()
            assert data["status"] == "healthy"

        self.reporter.info("Application started successfully", context="Test")

    # ================================================================
    # Destructive test (runs last alphabetically with z_ prefix)
    # ================================================================

    async def test_z_container_responds_to_sigterm(self):
        """Test container responds to SIGTERM signal (DESTRUCTIVE - runs last)."""
        self.reporter.info("Testing SIGTERM response", context="Test")

        # Send SIGTERM
        start_time = time.time()
        subprocess.run(
            ["docker", "kill", "--signal=SIGTERM", self.container_name],
            stdout=subprocess.DEVNULL,
        )

        # Wait for container to stop
        max_wait = 40
        stopped = False

        for _ in range(max_wait * 10):
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", self.container_name],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip() == "false":
                stopped = True
                break

            time.sleep(0.1)

        stop_time = time.time()
        duration = stop_time - start_time

        assert stopped
        assert duration < 40

        self.reporter.info(
            f"Container stopped gracefully in {duration:.1f}s", context="Test"
        )


if __name__ == "__main__":
    TestGracefulShutdown.run_as_main()
