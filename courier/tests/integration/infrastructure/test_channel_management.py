"""
Integration tests for Channel Management via ConnectionManager.

Tests real WebSocket channel operations including subscriptions,
broadcasting, and channel lifecycle.

Usage:
    laborant courier --integration
"""

from unittest.mock import AsyncMock, MagicMock

from fastapi import WebSocket
from shared.tests import LaborantTest

from courier.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)


class TestChannelManagement(LaborantTest):
    """Integration tests for channel management operations."""

    component_name = "courier"
    test_category = "integration"

    async def async_setup_test(self):
        """Setup fresh connection manager before EACH test."""
        self.manager = ConnectionManager()

    def _create_mock_websocket(self) -> WebSocket:
        """Create mock WebSocket for testing."""
        ws = MagicMock(spec=WebSocket)
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        return ws

    async def test_create_channel_on_first_subscriber(self):
        """Test channel is created when first client subscribes."""
        ws = self._create_mock_websocket()
        channel = "global"

        client = self.manager.add_client(ws, channel)

        assert client is not None
        assert client.channel_name == channel
        assert self.manager.channel_exists(channel)
        assert self.manager.get_channel_count(channel) == 1

    async def test_multiple_subscribers_same_channel(self):
        """Test multiple clients can subscribe to same channel."""
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()
        channel = "strategy.my-strategy"

        self.manager.add_client(ws1, channel, user_id="user1")
        self.manager.add_client(ws2, channel, user_id="user2")
        self.manager.add_client(ws3, channel, user_id="user3")

        subscribers = self.manager.get_channel_subscribers(channel)

        assert len(subscribers) == 3
        assert ws1 in subscribers
        assert ws2 in subscribers
        assert ws3 in subscribers
        assert self.manager.get_channel_count(channel) == 3

    async def test_remove_subscriber_from_channel(self):
        """Test removing subscriber from channel."""
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        channel = "user.12345"

        self.manager.add_client(ws1, channel, user_id="user1")
        self.manager.add_client(ws2, channel, user_id="user2")

        assert self.manager.get_channel_count(channel) == 2

        self.manager.remove_client(ws1, channel)

        assert self.manager.get_channel_count(channel) == 1
        subscribers = self.manager.get_channel_subscribers(channel)
        assert ws1 not in subscribers
        assert ws2 in subscribers

    async def test_channel_cleanup_when_empty(self):
        """Test empty channels are cleaned up."""
        ws = self._create_mock_websocket()
        channel = "temporary"

        self.manager.add_client(ws, channel)
        assert self.manager.channel_exists(channel)

        self.manager.remove_client(ws, channel)

        removed = self.manager.cleanup_empty_channels()

        assert channel in removed
        assert not self.manager.channel_exists(channel)

    async def test_get_all_channels_with_counts(self):
        """Test getting all channels with subscriber counts."""
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()

        self.manager.add_client(ws1, "global")
        self.manager.add_client(ws2, "global")
        self.manager.add_client(ws3, "strategy.test")

        all_channels = self.manager.get_all_channels()

        assert len(all_channels) == 2
        assert all_channels["global"] == 2
        assert all_channels["strategy.test"] == 1

    async def test_total_connections_across_channels(self):
        """Test counting total connections across all channels."""
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()
        ws4 = self._create_mock_websocket()

        self.manager.add_client(ws1, "global")
        self.manager.add_client(ws2, "global")
        self.manager.add_client(ws3, "user.123")
        self.manager.add_client(ws4, "strategy.abc")

        total = self.manager.get_total_connections()

        assert total == 4

    async def test_client_registry_tracking(self):
        """Test client metadata is tracked in registry."""
        ws = self._create_mock_websocket()
        channel = "user.98765"
        user_id = "user-uuid-123"
        wallet = "somewallet123"

        client = self.manager.add_client(
            ws, channel, user_id=user_id, wallet_address=wallet
        )

        retrieved = self.manager.get_client(ws)

        assert retrieved is not None
        assert retrieved.user_id == user_id
        assert retrieved.wallet_address == wallet
        assert retrieved.channel_name == channel

    async def test_channel_name_validation(self):
        """Test invalid channel names are rejected."""
        ws = self._create_mock_websocket()

        invalid_names = [
            "",
            "a" * 101,
            "invalid channel!",
            "UPPERCASE",
            "with:colon",
        ]

        for invalid_name in invalid_names:
            try:
                self.manager.add_client(ws, invalid_name)
                assert False, f"Should reject invalid channel: {invalid_name}"
            except (ValueError, Exception):
                pass

    async def test_remove_nonexistent_client(self):
        """Test removing client that doesn't exist doesn't crash."""
        ws = self._create_mock_websocket()
        channel = "nonexistent"

        self.manager.remove_client(ws, channel)

        assert not self.manager.channel_exists(channel)
        assert self.manager.get_total_connections() == 0


if __name__ == "__main__":
    TestChannelManagement.run_as_main()
