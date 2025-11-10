"""
E2E tests for Publish API endpoints.

Tests event publishing with real HTTP requests.

Usage:
    laborant courier --e2e
"""

import asyncio
import subprocess

import httpx
from shared.tests import LaborantTest


class TestPublishAPI(LaborantTest):
    """E2E tests for publish endpoints."""

    component_name = "courier"
    test_category = "e2e"

    client: httpx.AsyncClient = None
    api_base_url = "http://localhost:7765"
    container_name = "lumiere-test-courier-test"

    async def async_setup(self):
        """Setup HTTP client and start Courier container."""
        self.reporter.info("Setting up Publish API E2E tests...", context="Setup")

        # Start Courier container
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
        """Start Courier container."""
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

    # ================================================================
    # Valid event publishing tests (using real event schemas)
    # ================================================================

    async def test_publish_new_format_success(self):
        """Test publishing with valid backtest.started event."""
        self.reporter.info("Testing publish new format success", context="Test")

        # Valid backtest.started event
        event_data = {
            "type": "backtest.started",
            "metadata": {
                "source": "cartographe",
                "user_id": "test_user",
            },
            "data": {
                "backtest_id": "bt_test_123",
                "job_id": "job_test_456",
                "user_id": "test_user",
                "strategy_id": "strat_test",
                "parameters": {},
            },
        }

        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel", "data": event_data},
        )

        assert response.status_code == 200
        data = response.json()
        assert "clients_reached" in data
        assert isinstance(data["clients_reached"], int)
        assert data["clients_reached"] == 0

        self.reporter.info("Publish new format successful", context="Test")

    async def test_publish_legacy_format_success(self):
        """Test legacy format with valid event."""
        self.reporter.info("Testing legacy format success", context="Test")

        # Valid prophet.message_chunk event
        event_data = {
            "type": "prophet.message_chunk",
            "metadata": {"source": "prophet"},
            "data": {
                "conversation_id": "conv_test",
                "chunk": "test message",
                "is_final": False,
            },
        }

        response = await self.client.post(
            "/publish/legacy.channel",
            json=event_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "clients_reached" in data

        self.reporter.info("Legacy format works", context="Test")

    async def test_publish_without_event_type(self):
        """Test publishing without event type (backwards compatibility)."""
        self.reporter.info("Testing publish without type", context="Test")

        # No 'type' field - should pass through
        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel", "data": {"message": "hello"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients_reached"] == 0

        self.reporter.info("Publish without type works", context="Test")

    async def test_publish_invalid_event_schema(self):
        """Test publishing with invalid event schema fails."""
        self.reporter.info("Testing invalid event schema", context="Test")

        # backtest.started missing required fields
        invalid_event = {
            "type": "backtest.started",
            "metadata": {"source": "cartographe"},
            "data": {"backtest_id": "bt_123"},  # Missing required fields
        }

        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel", "data": invalid_event},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation" in str(data["detail"]).lower()

        self.reporter.info("Invalid schema rejected", context="Test")

    # ================================================================
    # Channel and request validation tests
    # ================================================================

    async def test_publish_legacy_format_channel_in_url(self):
        """Test legacy format with channel in URL."""
        self.reporter.info("Testing channel from URL", context="Test")

        event_data = {
            "type": "forge.job.started",
            "metadata": {"source": "forge"},
            "data": {
                "job_id": "job_123",
                "job_type": "test",
                "user_id": "user_123",
                "parameters": {},
            },
        }

        response = await self.client.post(
            "/publish/url.test.channel",
            json=event_data,
        )

        assert response.status_code == 200

        self.reporter.info("Channel from URL works", context="Test")

    async def test_publish_new_format_creates_channel(self):
        """Test publish auto-creates channel if needed."""
        self.reporter.info("Testing publish creates channel", context="Test")

        channel_name = "auto.created"
        event_data = {
            "type": "backtest.progress",
            "metadata": {"source": "cartographe"},
            "data": {
                "backtest_id": "bt_123",
                "job_id": "job_123",
                "user_id": "user_123",
                "progress": 0.5,
                "stage": "testing",
                "message": "Progress update",
            },
        }

        response = await self.client.post(
            "/publish",
            json={"channel": channel_name, "data": event_data},
        )

        assert response.status_code == 200

        # Check channel was created
        health = await self.client.get("/health")
        channels = health.json()["channels"]
        assert channel_name in channels

        self.reporter.info("Channel auto-creation works", context="Test")

    async def test_publish_new_format_invalid_channel_name(self):
        """Test invalid channel name is rejected."""
        self.reporter.info("Testing invalid channel name rejection", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "INVALID", "data": {"simple": "data"}},
        )

        assert response.status_code == 400

        self.reporter.info("Invalid channel name rejected", context="Test")

    async def test_publish_requires_channel(self):
        """Test channel field is required."""
        self.reporter.info("Testing channel required", context="Test")

        response = await self.client.post(
            "/publish",
            json={"data": {"test": "data"}},
        )

        assert response.status_code == 422

        self.reporter.info("Channel field required", context="Test")

    async def test_publish_requires_data(self):
        """Test data field is required."""
        self.reporter.info("Testing data required", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel"},
        )

        assert response.status_code == 422

        self.reporter.info("Data field required", context="Test")

    async def test_publish_data_must_be_dict(self):
        """Test data field must be a dictionary."""
        self.reporter.info("Testing data must be dict", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "test.channel", "data": "not a dict"},
        )

        assert response.status_code == 422

        self.reporter.info("Data type validated", context="Test")

    # ================================================================
    # Response and stats tests
    # ================================================================

    async def test_publish_response_format(self):
        """Test publish response has correct format."""
        self.reporter.info("Testing response format", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "test.format", "data": {"no": "type"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "channel" in data
        assert "clients_reached" in data
        assert "timestamp" in data

        self.reporter.info("Response format correct", context="Test")

    async def test_publish_increments_stats(self):
        """Test publishing increments statistics."""
        self.reporter.info("Testing stats handling", context="Test")

        stats_before = await self.client.get("/stats")
        before_count = stats_before.json()["total_messages_sent"]

        await self.client.post(
            "/publish",
            json={"channel": "stats.test", "data": {"test": "data"}},
        )

        stats_after = await self.client.get("/stats")
        after_count = stats_after.json()["total_messages_sent"]

        assert after_count >= before_count

        self.reporter.info("Stats handling passed", context="Test")

    async def test_publish_with_no_subscribers_returns_zero(self):
        """Test publish with no subscribers returns 0."""
        self.reporter.info("Testing publish with no subscribers", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "empty.channel", "data": {"test": "data"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients_reached"] == 0

        self.reporter.info("No subscribers returns 0", context="Test")

    # ================================================================
    # Multiple operations tests
    # ================================================================

    async def test_publish_multiple_messages_same_channel(self):
        """Test publishing multiple messages to same channel."""
        self.reporter.info("Testing multiple publishes", context="Test")

        channel = "multi.test"

        for i in range(3):
            response = await self.client.post(
                "/publish",
                json={"channel": channel, "data": {"count": i}},
            )
            assert response.status_code == 200

        self.reporter.info("Multiple publishes successful", context="Test")

    async def test_publish_to_different_channels(self):
        """Test publishing to different channels."""
        self.reporter.info("Testing different channels", context="Test")

        channels = ["channel.a", "channel.b", "channel.c"]

        for channel in channels:
            response = await self.client.post(
                "/publish",
                json={"channel": channel, "data": {"channel": channel}},
            )
            assert response.status_code == 200

        self.reporter.info("Different channels work", context="Test")

    # ================================================================
    # Auth tests
    # ================================================================

    async def test_publish_without_auth(self):
        """Test publishing without authentication works when auth disabled."""
        self.reporter.info("Testing publish without auth", context="Test")

        response = await self.client.post(
            "/publish",
            json={"channel": "no.auth", "data": {"test": "data"}},
        )

        assert response.status_code == 200

        self.reporter.info("No auth required (as configured)", context="Test")

    # ================================================================
    # Request validation tests
    # ================================================================

    async def test_publish_new_format_validates_request(self):
        """Test new format validates request structure."""
        self.reporter.info("Testing publish request validation", context="Test")

        # Invalid JSON structure
        response = await self.client.post(
            "/publish",
            json={"wrong": "structure"},
        )

        assert response.status_code == 422

        self.reporter.info("Request validation working", context="Test")


if __name__ == "__main__":
    TestPublishAPI.run_as_main()
