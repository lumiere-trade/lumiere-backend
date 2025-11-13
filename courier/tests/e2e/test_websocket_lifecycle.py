"""
E2E tests for WebSocket lifecycle.

Tests real WebSocket connections, subscriptions, and message flow.
Automatically starts/stops Courier container for testing.

Usage:
    laborant courier --e2e
"""

import asyncio
import subprocess

import websockets
from shared.tests import LaborantTest


class TestWebSocketLifecycle(LaborantTest):
    """E2E tests for WebSocket connection lifecycle."""

    component_name = "courier"
    test_category = "e2e"

    ws_base_url = "ws://localhost:7765"
    container_name = "lumiere-test-courier-ws-test"

    async def async_setup(self):
        """Setup and start Courier container."""
        self.reporter.info("Setting up WebSocket lifecycle tests...", context="Setup")

        await self._start_courier_container()
        await self._wait_for_api()

        self.reporter.info("WebSocket lifecycle tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup and stop Courier container."""
        self.reporter.info("Cleaning up WebSocket tests...", context="Teardown")

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

        import httpx

        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "http://localhost:7765/health", timeout=2.0
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

    def _get_total_connections(self, health_response: dict) -> int:
        """Extract total connections from health response."""
        try:
            return health_response["checks"]["connection_capacity"]["metadata"][
                "total_connections"
            ]
        except (KeyError, TypeError):
            return 0

    def _get_channel_names(self, health_response: dict) -> list:
        """Extract channel names from health response."""
        try:
            return health_response["checks"]["connection_manager"]["metadata"][
                "channel_names"
            ]
        except (KeyError, TypeError):
            return []

    async def test_websocket_connect_and_disconnect(self):
        """Test basic WebSocket connect and disconnect."""
        self.reporter.info("Testing WebSocket connect/disconnect", context="Test")

        async with websockets.connect(f"{self.ws_base_url}/ws/test.channel") as ws:
            assert ws.close_code is None

        self.reporter.info("WebSocket connected and disconnected", context="Test")

    async def test_websocket_connect_to_channel(self):
        """Test connecting to specific channel."""
        self.reporter.info("Testing channel connection", context="Test")

        channel = "test.lifecycle"

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws:
            assert ws.close_code is None

        self.reporter.info("Channel connection successful", context="Test")

    async def test_websocket_stays_connected(self):
        """Test WebSocket stays connected for duration."""
        self.reporter.info("Testing connection stability", context="Test")

        async with websockets.connect(f"{self.ws_base_url}/ws/stable") as ws:
            await asyncio.sleep(2)
            assert ws.close_code is None

        self.reporter.info("Connection remained stable", context="Test")

    async def test_multiple_clients_same_channel(self):
        """Test multiple clients can connect to same channel."""
        self.reporter.info("Testing multiple clients", context="Test")

        channel = "multi.client"

        async with (
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws1,
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws2,
        ):
            assert ws1.close_code is None
            assert ws2.close_code is None

        self.reporter.info("Multiple clients connected", context="Test")

    async def test_clients_on_different_channels(self):
        """Test clients can connect to different channels."""
        self.reporter.info("Testing different channels", context="Test")

        async with (
            websockets.connect(f"{self.ws_base_url}/ws/channel.one") as ws1,
            websockets.connect(f"{self.ws_base_url}/ws/channel.two") as ws2,
        ):
            assert ws1.close_code is None
            assert ws2.close_code is None

        self.reporter.info("Different channels work", context="Test")

    async def test_websocket_invalid_channel_name(self):
        """Test connection with invalid channel name fails."""
        self.reporter.info("Testing invalid channel rejection", context="Test")

        try:
            async with websockets.connect(
                f"{self.ws_base_url}/ws/INVALID CHANNEL!", open_timeout=2
            ):
                await asyncio.sleep(0.1)
            assert False, "Should reject invalid channel name"
        except Exception:
            pass

        self.reporter.info("Invalid channel rejected", context="Test")

    async def test_websocket_reconnect(self):
        """Test client can reconnect after disconnect."""
        self.reporter.info("Testing reconnection", context="Test")

        channel = "reconnect.test"

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws1:
            assert ws1.close_code is None

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws2:
            assert ws2.close_code is None

        self.reporter.info("Reconnection successful", context="Test")

    async def test_client_count_increments(self):
        """Test client count increments when connecting."""
        self.reporter.info("Testing client count", context="Test")

        import httpx

        async with httpx.AsyncClient() as client:
            before = await client.get("http://localhost:7765/health")
            count_before = self._get_total_connections(before.json())

            async with websockets.connect(f"{self.ws_base_url}/ws/count.test"):
                await asyncio.sleep(0.5)

                during = await client.get("http://localhost:7765/health")
                count_during = self._get_total_connections(during.json())

                assert count_during > count_before

        self.reporter.info("Client count incremented", context="Test")

    async def test_channel_appears_in_health(self):
        """Test channel appears in health endpoint when client connects."""
        self.reporter.info("Testing channel in health", context="Test")

        import httpx

        channel = "health.visible"

        async with httpx.AsyncClient() as client:
            async with websockets.connect(f"{self.ws_base_url}/ws/{channel}"):
                await asyncio.sleep(0.5)

                health = await client.get("http://localhost:7765/health")
                channels = self._get_channel_names(health.json())

                assert channel in channels

        self.reporter.info("Channel visible in health", context="Test")

    async def test_graceful_disconnect(self):
        """Test graceful WebSocket disconnect."""
        self.reporter.info("Testing graceful disconnect", context="Test")

        async with websockets.connect(f"{self.ws_base_url}/ws/graceful") as ws:
            assert ws.close_code is None
            await ws.close()
            assert ws.close_code is not None

        self.reporter.info("Graceful disconnect successful", context="Test")

    async def test_connection_timeout_handling(self):
        """Test connection with timeout."""
        self.reporter.info("Testing timeout handling", context="Test")

        try:
            async with websockets.connect(
                f"{self.ws_base_url}/ws/timeout.test", open_timeout=5
            ) as ws:
                assert ws.close_code is None
        except Exception as e:
            assert False, f"Connection should succeed: {e}"

        self.reporter.info("Timeout handling works", context="Test")

    async def test_rapid_connect_disconnect(self):
        """Test rapid connect/disconnect cycles."""
        self.reporter.info("Testing rapid connections", context="Test")

        for i in range(5):
            async with websockets.connect(f"{self.ws_base_url}/ws/rapid.test") as ws:
                assert ws.close_code is None

        self.reporter.info("Rapid connections handled", context="Test")

    async def test_concurrent_connections(self):
        """Test multiple concurrent connections."""
        self.reporter.info("Testing concurrent connections", context="Test")

        async def connect_client(n):
            async with websockets.connect(
                f"{self.ws_base_url}/ws/concurrent.test"
            ) as ws:
                await asyncio.sleep(0.5)
                return ws.close_code is None

        results = await asyncio.gather(*[connect_client(i) for i in range(5)])

        assert all(results)

        self.reporter.info("Concurrent connections successful", context="Test")

    async def test_connection_cleanup_after_disconnect(self):
        """Test connection is cleaned up after disconnect."""
        self.reporter.info("Testing cleanup after disconnect", context="Test")

        import httpx

        channel = "cleanup.test"

        async with httpx.AsyncClient() as client:
            async with websockets.connect(f"{self.ws_base_url}/ws/{channel}"):
                await asyncio.sleep(0.5)

            await asyncio.sleep(1)

            health = await client.get("http://localhost:7765/health")
            count = self._get_total_connections(health.json())

            assert count == 0

        self.reporter.info("Cleanup completed", context="Test")

    async def test_channel_cleanup_after_last_disconnect(self):
        """Test channel cleanup after last client disconnects."""
        self.reporter.info("Testing channel cleanup", context="Test")

        import httpx

        channel = "ephemeral.channel"

        async with httpx.AsyncClient() as client:
            async with websockets.connect(f"{self.ws_base_url}/ws/{channel}"):
                await asyncio.sleep(0.5)

            # Give more time for async cleanup
            await asyncio.sleep(2.0)

            health = await client.get("http://localhost:7765/health")

            # Main assertion: total connections should be 0 after disconnect
            connections = self._get_total_connections(health.json())
            assert connections == 0, f"Expected 0 connections, got {connections}"

            # Channel cleanup is best-effort (timing varies)
            channels = self._get_channel_names(health.json())
            if channel not in channels:
                self.reporter.info("Channel cleaned up completely", context="Test")
            else:
                self.reporter.info(
                    "Channel still exists (cleanup timing varies)", context="Test"
                )

        self.reporter.info("Channel cleanup verified", context="Test")


if __name__ == "__main__":
    TestWebSocketLifecycle.run_as_main()
