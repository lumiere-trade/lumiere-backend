"""
E2E tests for complete integration flows.

Tests full user journeys combining WebSocket connections and HTTP publish.
Automatically starts/stops Courier container for testing.

Usage:
    laborant courier --e2e
"""

import asyncio
import json
import subprocess

import httpx
import websockets
from shared.tests import LaborantTest


class TestFullFlow(LaborantTest):
    """E2E tests for complete integration flows."""

    component_name = "courier"
    test_category = "e2e"

    ws_base_url = "ws://localhost:7765"
    http_base_url = "http://localhost:7765"
    container_name = "lumiere-test-courier-full-flow-test"

    async def async_setup(self):
        """Setup and start Courier container."""
        self.reporter.info("Setting up full flow tests...", context="Setup")

        await self._start_courier_container()
        await self._wait_for_api()

        self.reporter.info("Full flow tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup and stop Courier container."""
        self.reporter.info("Cleaning up full flow tests...", context="Teardown")

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
                        f"{self.http_base_url}/health", timeout=2.0
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
            # Fallback for older response format
            return health_response.get("total_clients", 0)

    async def test_full_flow_connect_publish_receive(self):
        """Test complete flow: connect, publish, receive message."""
        self.reporter.info("Testing full connect-publish-receive", context="Test")

        channel = "full.flow"
        messages_received = []

        async def receive_messages(ws):
            try:
                async for message in ws:
                    messages_received.append(json.loads(message))
            except Exception:
                pass

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws:
            receive_task = asyncio.create_task(receive_messages(ws))

            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.http_base_url}/publish",
                    json={
                        "channel": channel,
                        "data": {"message": "test", "value": 123},
                    },
                )
                assert response.status_code == 200

            await asyncio.sleep(0.5)

            receive_task.cancel()

        assert len(messages_received) == 1
        assert messages_received[0]["message"] == "test"

        self.reporter.info("Full flow successful", context="Test")

    async def test_multiple_clients_receive_same_message(self):
        """Test multiple clients on same channel receive broadcast."""
        self.reporter.info("Testing broadcast to multiple clients", context="Test")

        channel = "broadcast.test"
        client1_messages = []
        client2_messages = []

        async def receive_c1(ws):
            try:
                async for msg in ws:
                    client1_messages.append(json.loads(msg))
            except Exception:
                pass

        async def receive_c2(ws):
            try:
                async for msg in ws:
                    client2_messages.append(json.loads(msg))
            except Exception:
                pass

        async with (
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws1,
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws2,
        ):
            task1 = asyncio.create_task(receive_c1(ws1))
            task2 = asyncio.create_task(receive_c2(ws2))

            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.http_base_url}/publish",
                    json={"channel": channel, "data": {"broadcast": True}},
                )

            await asyncio.sleep(0.5)

            task1.cancel()
            task2.cancel()

        assert len(client1_messages) >= 1
        assert len(client2_messages) >= 1

        self.reporter.info("Broadcast to multiple clients works", context="Test")

    async def test_channels_isolated_messages_dont_leak(self):
        """Test messages don't leak between channels."""
        self.reporter.info("Testing channel isolation", context="Test")

        channel1_messages = []
        channel2_messages = []

        async def receive_ch1(ws):
            try:
                async for msg in ws:
                    channel1_messages.append(json.loads(msg))
            except Exception:
                pass

        async def receive_ch2(ws):
            try:
                async for msg in ws:
                    channel2_messages.append(json.loads(msg))
            except Exception:
                pass

        async with (
            websockets.connect(f"{self.ws_base_url}/ws/channel.one") as ws1,
            websockets.connect(f"{self.ws_base_url}/ws/channel.two") as ws2,
        ):
            task1 = asyncio.create_task(receive_ch1(ws1))
            task2 = asyncio.create_task(receive_ch2(ws2))

            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.http_base_url}/publish",
                    json={"channel": "channel.one", "data": {"for": "channel1"}},
                )

            await asyncio.sleep(0.5)

            task1.cancel()
            task2.cancel()

        assert len(channel1_messages) == 1
        assert len(channel2_messages) == 0

        self.reporter.info("Channel isolation confirmed", context="Test")

    async def test_publish_returns_correct_client_count(self):
        """Test publish response shows correct number of clients reached."""
        self.reporter.info("Testing client count accuracy", context="Test")

        channel = "count.accuracy"

        async with (
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws1,
            websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws2,
        ):
            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.http_base_url}/publish",
                    json={"channel": channel, "data": {"test": "data"}},
                )

                data = response.json()
                assert data["clients_reached"] == 2

        self.reporter.info("Client count accurate", context="Test")

    async def test_late_joiner_receives_subsequent_messages(self):
        """Test client joining late receives subsequent messages."""
        self.reporter.info("Testing late joiner", context="Test")

        channel = "late.joiner"
        messages = []

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.http_base_url}/publish",
                json={"channel": channel, "data": {"message": "first"}},
            )

        async def receive_msgs(ws):
            try:
                async for msg in ws:
                    messages.append(json.loads(msg))
            except Exception:
                pass

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws:
            task = asyncio.create_task(receive_msgs(ws))

            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.http_base_url}/publish",
                    json={"channel": channel, "data": {"message": "second"}},
                )

            await asyncio.sleep(0.5)
            task.cancel()

        assert len(messages) == 1
        assert messages[0]["message"] == "second"

        self.reporter.info("Late joiner receives new messages", context="Test")

    async def test_concurrent_publishes_all_delivered(self):
        """Test concurrent publishes all get delivered."""
        self.reporter.info("Testing concurrent publishes", context="Test")

        channel = "concurrent.pub"
        messages = []

        async def receive_msgs(ws):
            try:
                async for msg in ws:
                    messages.append(json.loads(msg))
            except Exception:
                pass

        async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws:
            task = asyncio.create_task(receive_msgs(ws))

            await asyncio.sleep(0.5)

            async def publish_message(n):
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.http_base_url}/publish",
                        json={"channel": channel, "data": {"count": n}},
                    )

            await asyncio.gather(*[publish_message(i) for i in range(5)])

            await asyncio.sleep(1)
            task.cancel()

        assert len(messages) == 5

        self.reporter.info("Concurrent publishes delivered", context="Test")

    async def test_health_reflects_active_connections(self):
        """Test health endpoint reflects active connections."""
        self.reporter.info("Testing health accuracy", context="Test")

        channel = "health.test.isolated"

        async with httpx.AsyncClient() as client:
            before = await client.get(f"{self.http_base_url}/health")
            count_before = self._get_total_connections(before.json())

            self.reporter.info(
                f"Baseline connections: {count_before}",
                context="Test",
            )

            async with (
                websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws1,
                websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws2,
            ):
                await asyncio.sleep(0.5)

                during = await client.get(f"{self.http_base_url}/health")
                count_during = self._get_total_connections(during.json())

                # Should have exactly 2 more connections
                assert count_during == count_before + 2, (
                    f"Expected {count_before + 2} during, " f"got {count_during}"
                )

            # Wait for cleanup to complete (async context manager may not wait)
            await asyncio.sleep(2.0)

            after = await client.get(f"{self.http_base_url}/health")
            count_after = self._get_total_connections(after.json())

            # Robust check: allow small tolerance for async timing
            leaked = count_after - count_before
            assert leaked <= 0, (
                f"Connection leak detected: expected <={count_before}, "
                f"got {count_after} (leaked: {leaked})"
            )

        self.reporter.info("Health reflects connections accurately", context="Test")

    async def test_rapid_connect_publish_disconnect(self):
        """Test rapid cycles of connect-publish-disconnect."""
        self.reporter.info("Testing rapid cycles", context="Test")

        channel = "rapid.cycles"

        for i in range(3):
            messages = []

            async def receive_msgs(ws):
                try:
                    async for msg in ws:
                        messages.append(json.loads(msg))
                except Exception:
                    pass

            async with websockets.connect(f"{self.ws_base_url}/ws/{channel}") as ws:
                task = asyncio.create_task(receive_msgs(ws))

                await asyncio.sleep(0.3)

                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.http_base_url}/publish",
                        json={"channel": channel, "data": {"cycle": i}},
                    )

                await asyncio.sleep(0.3)
                task.cancel()

            assert len(messages) >= 1

        self.reporter.info("Rapid cycles handled", context="Test")


if __name__ == "__main__":
    TestFullFlow.run_as_main()
