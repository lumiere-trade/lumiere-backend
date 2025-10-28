"""
E2E tests for Health and Stats API endpoints.

Tests real HTTP endpoints with running Courier service.
Automatically starts/stops Courier container for testing.

Usage:
    laborant courier --e2e
"""

import asyncio
import subprocess

import httpx
from shared.tests import LaborantTest


class TestHealthAPI(LaborantTest):
    """E2E tests for health and statistics endpoints."""

    component_name = "courier"
    test_category = "e2e"

    client: httpx.AsyncClient = None
    api_base_url = "http://localhost:7765"
    container_name = "courier-e2e-test"

    async def async_setup(self):
        """Setup HTTP client and start Courier container."""
        self.reporter.info("Setting up Health API E2E tests...", context="Setup")

        # Start Courier container for testing
        await self._start_courier_container()

        # Wait for Courier to be ready
        await self._wait_for_api()

        TestHealthAPI.client = httpx.AsyncClient(base_url=self.api_base_url)
        self.reporter.info("Health API E2E tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup HTTP client and stop Courier container."""
        self.reporter.info("Cleaning up Health API tests...", context="Teardown")

        if TestHealthAPI.client:
            await TestHealthAPI.client.aclose()

        # Stop and remove Courier container
        await self._stop_courier_container()

        self.reporter.info("Cleanup complete", context="Teardown")

    async def _start_courier_container(self):
        """Start Courier container for testing."""
        self.reporter.info("Starting Courier container...", context="Setup")

        # Stop any existing test container
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Start Courier container
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-p",
                "7765:7765",
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

        self.reporter.info("Courier container started", context="Setup")

    async def _stop_courier_container(self):
        """Stop and remove Courier container."""
        self.reporter.info("Stopping Courier container...", context="Teardown")

        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.reporter.info("Courier container stopped", context="Teardown")

    async def _wait_for_api(self):
        """Wait for API to be ready."""
        self.reporter.info("Waiting for Courier API...", context="Setup")

        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.api_base_url}/health", timeout=2.0
                    )
                    if response.status_code == 200:
                        self.reporter.info(
                            f"Courier API ready (attempt {attempt + 1})",
                            context="Setup",
                        )
                        return
            except Exception:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        raise RuntimeError("Courier API not accessible after 30 seconds")

    async def test_health_check_returns_200(self):
        """Test health endpoint returns 200."""
        self.reporter.info("Testing health check returns 200", context="Test")

        response = await self.client.get("/health")

        assert response.status_code == 200

        self.reporter.info("Health check returned 200", context="Test")

    async def test_health_check_includes_status(self):
        """Test health response includes status field."""
        self.reporter.info("Testing health includes status", context="Test")

        response = await self.client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

        self.reporter.info("Health status field present", context="Test")

    async def test_health_check_includes_uptime(self):
        """Test health response includes uptime."""
        self.reporter.info("Testing health includes uptime", context="Test")

        response = await self.client.get("/health")
        data = response.json()

        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

        self.reporter.info("Health uptime field present", context="Test")

    async def test_health_check_includes_total_clients(self):
        """Test health response includes client count."""
        self.reporter.info("Testing health includes client count", context="Test")

        response = await self.client.get("/health")
        data = response.json()

        assert "total_clients" in data
        assert isinstance(data["total_clients"], int)
        assert data["total_clients"] >= 0

        self.reporter.info("Health client count present", context="Test")

    async def test_health_check_includes_channels(self):
        """Test health response includes channels dict."""
        self.reporter.info("Testing health includes channels", context="Test")

        response = await self.client.get("/health")
        data = response.json()

        assert "channels" in data
        assert isinstance(data["channels"], dict)

        self.reporter.info("Health channels field present", context="Test")

    async def test_stats_returns_200(self):
        """Test stats endpoint returns 200."""
        self.reporter.info("Testing stats returns 200", context="Test")

        response = await self.client.get("/stats")

        assert response.status_code == 200

        self.reporter.info("Stats returned 200", context="Test")

    async def test_stats_includes_uptime(self):
        """Test stats includes uptime."""
        self.reporter.info("Testing stats includes uptime", context="Test")

        response = await self.client.get("/stats")
        data = response.json()

        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))

        self.reporter.info("Stats uptime present", context="Test")

    async def test_stats_includes_connection_count(self):
        """Test stats includes connection count."""
        self.reporter.info("Testing stats includes connections", context="Test")

        response = await self.client.get("/stats")
        data = response.json()

        assert "total_connections" in data
        assert isinstance(data["total_connections"], int)

        self.reporter.info("Stats connection count present", context="Test")

    async def test_stats_includes_message_counts(self):
        """Test stats includes message counts."""
        self.reporter.info("Testing stats includes message counts", context="Test")

        response = await self.client.get("/stats")
        data = response.json()

        assert "total_messages_sent" in data
        assert "total_messages_received" in data
        assert isinstance(data["total_messages_sent"], int)
        assert isinstance(data["total_messages_received"], int)

        self.reporter.info("Stats message counts present", context="Test")

    async def test_stats_includes_active_clients(self):
        """Test stats includes active clients."""
        self.reporter.info("Testing stats includes active clients", context="Test")

        response = await self.client.get("/stats")
        data = response.json()

        assert "active_clients" in data
        assert isinstance(data["active_clients"], int)

        self.reporter.info("Stats active clients present", context="Test")

    async def test_stats_includes_channel_details(self):
        """Test stats includes channel details."""
        self.reporter.info("Testing stats includes channel details", context="Test")

        response = await self.client.get("/stats")
        data = response.json()

        assert "channels" in data
        assert isinstance(data["channels"], dict)

        self.reporter.info("Stats channel details present", context="Test")

    async def test_health_check_valid_json(self):
        """Test health returns valid JSON."""
        self.reporter.info("Testing health returns valid JSON", context="Test")

        response = await self.client.get("/health")

        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

        self.reporter.info("Health returns valid JSON", context="Test")

    async def test_stats_valid_json(self):
        """Test stats returns valid JSON."""
        self.reporter.info("Testing stats returns valid JSON", context="Test")

        response = await self.client.get("/stats")

        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

        self.reporter.info("Stats returns valid JSON", context="Test")


if __name__ == "__main__":
    TestHealthAPI.run_as_main()
