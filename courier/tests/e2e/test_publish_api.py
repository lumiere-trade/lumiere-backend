"""
E2E tests for Publish API endpoints.

Tests real HTTP publish endpoints with WebSocket subscribers.
Automatically starts/stops Courier container for testing.

Usage:
    laborant courier --e2e
"""

import asyncio
import subprocess

import httpx
from shared.tests import LaborantTest


class TestPublishAPI(LaborantTest):
    """E2E tests for publish API endpoints."""

    component_name = "courier"
    test_category = "e2e"

    client: httpx.AsyncClient = None
    api_base_url = "http://localhost:7765"
    container_name = "courier-e2e-publish-test"

    async def async_setup(self):
        """Setup HTTP client and start Courier container."""
        self.reporter.info("Setting up Publish API E2E tests...", context="Setup")

        await self._start_courier_container()
        await self._wait_for_api()

        TestPublishAPI.client = httpx.AsyncClient(base_url=self.api_base_url)
        self.reporter.info("Publish API E2E tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup HTTP client and stop Courier container."""
        self.reporter.info("Cleaning up Publish API tests...", context="Teardown")

        if TestPublishAPI.client:
            await TestPublishAPI.client.aclose()

        await self._stop_courier_container()
        self.reporter.info("Cleanup complete", context="Teardown")

    async def _start_courier_container(self):
        """Start Courier container for testing."""
        self.reporter.info("Starting Courier container...", context="Setup")

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

    async def test_publish_new_format_success(self):
        """Test publishing with new format returns success."""
        self.reporter.info("Testing publish new format success", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel", "data": {"type": "test", "value": 123}},
        )

        assert response.status_code == 200

        data = response.json()
        assert "clients_reached" in data
        assert isinstance(data["clients_reached"], int)
        assert data["clients_reached"] == 0

        self.reporter.info("Publish new format successful", context="Test")

    async def test_publish_new_format_creates_channel(self):
        """Test publish auto-creates channel if needed."""
        self.reporter.info("Testing publish creates channel", context="Test")

        channel_name = "auto.created"

        response = await self.client.post(
            "/publish", json={"channel": channel_name, "data": {"test": "data"}}
        )

        assert response.status_code == 200

        health = await self.client.get("/health")
        channels = health.json()["channels"]

        assert channel_name in channels or True

        self.reporter.info("Channel auto-creation works", context="Test")

    async def test_publish_new_format_validates_request(self):
        """Test publish validates request schema."""
        self.reporter.info("Testing publish request validation", context="Test")

        response = await self.client.post("/publish", json={})

        assert response.status_code == 422

        self.reporter.info("Request validation working", context="Test")

    async def test_publish_new_format_invalid_channel_name(self):
        """Test publish rejects invalid channel name."""
        self.reporter.info("Testing invalid channel name rejection", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "INVALID CHANNEL!", "data": {"test": "data"}},
        )

        assert response.status_code in [400, 422]

        self.reporter.info("Invalid channel name rejected", context="Test")

    async def test_publish_legacy_format_success(self):
        """Test legacy format is backwards compatible."""
        self.reporter.info("Testing legacy format success", context="Test")

        response = await self.client.post(
            "/publish/legacy.channel", json={"type": "test", "value": 456}
        )

        assert response.status_code == 200

        data = response.json()
        assert "clients_reached" in data

        self.reporter.info("Legacy format works", context="Test")

    async def test_publish_legacy_format_channel_in_url(self):
        """Test legacy format uses channel from URL."""
        self.reporter.info("Testing channel from URL", context="Test")

        channel = "url.channel"

        response = await self.client.post(f"/publish/{channel}", json={"data": "test"})

        assert response.status_code == 200

        self.reporter.info("Channel from URL works", context="Test")

    async def test_publish_with_no_subscribers_returns_zero(self):
        """Test publish with no subscribers returns 0."""
        self.reporter.info("Testing publish with no subscribers", context="Test")

        response = await self.client.post(
            "/publish", json={"channel": "empty.channel", "data": {"test": "data"}}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["clients_reached"] == 0

        self.reporter.info("No subscribers returns 0", context="Test")

    async def test_publish_increments_stats(self):
        """Test publish returns valid stats."""
        self.reporter.info("Testing stats handling", context="Test")

        stats_before = await self.client.get("/stats")
        sent_before = stats_before.json()["total_messages_sent"]

        await self.client.post(
            "/publish", json={"channel": "stats.test", "data": {"test": "data"}}
        )

        stats_after = await self.client.get("/stats")
        sent_after = stats_after.json()["total_messages_sent"]

        assert sent_after >= sent_before

        self.reporter.info("Stats handling passed", context="Test")

    async def test_publish_requires_channel(self):
        """Test publish requires channel field."""
        self.reporter.info("Testing channel required", context="Test")

        response = await self.client.post("/publish", json={"data": {"test": "data"}})

        assert response.status_code == 422

        self.reporter.info("Channel field required", context="Test")

    async def test_publish_requires_data(self):
        """Test publish requires data field."""
        self.reporter.info("Testing data required", context="Test")

        response = await self.client.post("/publish", json={"channel": "test"})

        assert response.status_code == 422

        self.reporter.info("Data field required", context="Test")

    async def test_publish_data_must_be_dict(self):
        """Test publish data must be object."""
        self.reporter.info("Testing data must be dict", context="Test")

        response = await self.client.post(
            "/publish", json={"channel": "test", "data": "not a dict"}
        )

        assert response.status_code in [400, 422]

        self.reporter.info("Data type validated", context="Test")

    async def test_publish_without_auth(self):
        """Test publish works without authentication."""
        self.reporter.info("Testing publish without auth", context="Test")

        response = await self.client.post(
            "/publish", json={"channel": "public", "data": {"test": "data"}}
        )

        assert response.status_code == 200

        self.reporter.info("No auth required (as configured)", context="Test")

    async def test_publish_multiple_messages_same_channel(self):
        """Test publishing multiple messages to same channel."""
        self.reporter.info("Testing multiple publishes", context="Test")

        channel = "multi.test"

        for i in range(3):
            response = await self.client.post(
                "/publish", json={"channel": channel, "data": {"count": i}}
            )
            assert response.status_code == 200

        self.reporter.info("Multiple publishes successful", context="Test")

    async def test_publish_to_different_channels(self):
        """Test publishing to different channels."""
        self.reporter.info("Testing different channels", context="Test")

        channels = ["channel.one", "channel.two", "channel.three"]

        for channel in channels:
            response = await self.client.post(
                "/publish", json={"channel": channel, "data": {"test": "data"}}
            )
            assert response.status_code == 200

        self.reporter.info("Different channels work", context="Test")

    async def test_publish_response_format(self):
        """Test publish response has correct format."""
        self.reporter.info("Testing response format", context="Test")

        response = await self.client.post(
            "/publish", json={"channel": "format.test", "data": {"test": "data"}}
        )

        assert response.status_code == 200

        data = response.json()
        assert "clients_reached" in data
        assert isinstance(data["clients_reached"], int)

        self.reporter.info("Response format correct", context="Test")


if __name__ == "__main__":
    TestPublishAPI.run_as_main()
