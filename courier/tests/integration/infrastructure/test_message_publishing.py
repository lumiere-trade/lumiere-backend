"""
Integration tests for Message Publishing and Broadcasting.

Tests real message delivery through ConnectionManager and
BroadcastMessageUseCase with mock WebSocket connections.

Usage:
    laborant courier --integration
"""

from unittest.mock import AsyncMock, MagicMock

from fastapi import WebSocket
from shared.tests import LaborantTest

from courier.application.use_cases.broadcast_message import (
    BroadcastMessageUseCase,
)
from courier.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)


class TestMessagePublishing(LaborantTest):
    """Integration tests for message publishing operations."""

    component_name = "courier"
    test_category = "integration"

    async def async_setup(self):
        """Setup components for each test."""
        self.reporter.info("Setting up message publishing tests...", context="Setup")
        self.manager = ConnectionManager()
        self.broadcast_use_case = BroadcastMessageUseCase()
        self.reporter.info("Message publishing tests ready", context="Setup")

    async def async_teardown(self):
        """Cleanup after each test."""
        self.reporter.info(
            "Cleaning up message publishing tests...", context="Teardown"
        )
        if hasattr(self, "manager"):
            self.manager.channels = {}
            self.manager.client_registry = {}
        self.reporter.info("Cleanup complete", context="Teardown")

    def _create_mock_websocket(self) -> WebSocket:
        """Create mock WebSocket for testing."""
        ws = MagicMock(spec=WebSocket)
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        return ws

    async def test_broadcast_to_single_subscriber(self):
        """Test broadcasting message to single subscriber."""
        self.reporter.info("Testing broadcast to single subscriber", context="Test")

        ws = self._create_mock_websocket()
        channel = "test.single"

        self.manager.add_client(ws, channel)
        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "update", "data": {"status": "active"}}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 1
        assert ws.send_json.called
        assert ws.send_json.call_count == 1

        self.reporter.info("Message broadcast successfully", context="Test")

    async def test_broadcast_to_multiple_subscribers(self):
        """Test broadcasting message to multiple subscribers."""
        self.reporter.info("Testing broadcast to multiple subscribers", context="Test")

        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()
        channel = "strategy.trading"

        self.manager.add_client(ws1, channel, user_id="user1")
        self.manager.add_client(ws2, channel, user_id="user2")
        self.manager.add_client(ws3, channel, user_id="user3")

        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "price_update", "price": 1234.56}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 3
        assert ws1.send_json.call_count == 1
        assert ws2.send_json.call_count == 1
        assert ws3.send_json.call_count == 1

        self.reporter.info("Broadcast to all subscribers successful", context="Test")

    async def test_broadcast_to_empty_channel(self):
        """Test broadcasting to channel with no subscribers."""
        self.reporter.info("Testing broadcast to empty channel", context="Test")

        channel = "empty.channel"
        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "notification", "text": "Hello"}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 0

        self.reporter.info("Empty channel handled correctly", context="Test")

    async def test_broadcast_with_dead_connection(self):
        """Test broadcasting skips dead connections."""
        self.reporter.info("Testing broadcast with dead connection", context="Test")

        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()
        channel = "user.123"

        ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        self.manager.add_client(ws1, channel)
        self.manager.add_client(ws2, channel)
        self.manager.add_client(ws3, channel)

        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "alert", "message": "Important update"}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 2
        assert ws1.send_json.call_count == 1
        assert ws2.send_json.call_count == 1
        assert ws3.send_json.call_count == 1

        self.reporter.info("Dead connection skipped successfully", context="Test")

    async def test_broadcast_message_validation(self):
        """Test message data validation during broadcast."""
        self.reporter.info("Testing message validation", context="Test")

        ws = self._create_mock_websocket()
        channel = "global"

        self.manager.add_client(ws, channel)
        subscribers = self.manager.get_channel_subscribers(channel)

        try:
            await self.broadcast_use_case.execute(channel, {}, subscribers)
            assert False, "Should reject empty message"
        except ValueError:
            pass

        self.reporter.info("Message validation working", context="Test")

    async def test_broadcast_different_message_types(self):
        """Test broadcasting different message types."""
        self.reporter.info("Testing different message types", context="Test")

        ws = self._create_mock_websocket()
        channel = "test.types"

        self.manager.add_client(ws, channel)
        subscribers = self.manager.get_channel_subscribers(channel)

        price_msg = {"type": "price", "token": "SOL", "value": 123.45}
        sent = await self.broadcast_use_case.execute(channel, price_msg, subscribers)
        assert sent == 1

        trade_msg = {"type": "trade", "size": 1000, "status": "executed"}
        sent = await self.broadcast_use_case.execute(channel, trade_msg, subscribers)
        assert sent == 1

        notif_msg = {"type": "notification", "text": "System maintenance"}
        sent = await self.broadcast_use_case.execute(channel, notif_msg, subscribers)
        assert sent == 1

        assert ws.send_json.call_count == 3

        self.reporter.info(
            "Different message types broadcast successfully", context="Test"
        )

    async def test_broadcast_to_specific_user_channel(self):
        """Test broadcasting to user-specific channel."""
        self.reporter.info("Testing user-specific channel broadcast", context="Test")

        ws = self._create_mock_websocket()
        user_id = "user-abc-123"
        channel = f"user.{user_id}"

        self.manager.add_client(ws, channel, user_id=user_id)
        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "personal", "data": "Your balance: $1000"}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 1
        assert ws.send_json.call_count == 1

        self.reporter.info("User-specific broadcast successful", context="Test")

    async def test_broadcast_to_strategy_channel(self):
        """Test broadcasting to strategy-specific channel."""
        self.reporter.info("Testing strategy channel broadcast", context="Test")

        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        strategy_id = "momentum-v2"
        channel = f"strategy.{strategy_id}"

        self.manager.add_client(ws1, channel, user_id="owner")
        self.manager.add_client(ws2, channel, user_id="viewer")

        subscribers = self.manager.get_channel_subscribers(channel)

        message = {"type": "signal", "action": "BUY", "symbol": "SOL"}
        sent_count = await self.broadcast_use_case.execute(
            channel, message, subscribers
        )

        assert sent_count == 2
        assert ws1.send_json.call_count == 1
        assert ws2.send_json.call_count == 1

        self.reporter.info("Strategy channel broadcast successful", context="Test")


if __name__ == "__main__":
    TestMessagePublishing.run_as_main()
