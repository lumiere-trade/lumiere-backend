"""
Integration tests for ConnectionManager.

Tests WebSocket connection management with mock WebSocket objects.

Usage:
    python -m courier.tests.integration.infrastructure.test_connection_manager
    laborant courier --integration
"""

from unittest.mock import Mock

from shared.tests import LaborantTest

from courier.domain.entities import Client
from courier.infrastructure.websocket.connection_manager import ConnectionManager


class TestConnectionManager(LaborantTest):
    """Integration tests for ConnectionManager."""

    component_name = "courier"
    test_category = "integration"

    def _create_mock_websocket(self) -> Mock:
        """Create mock WebSocket object."""
        return Mock()

    # ================================================================
    # Client management tests
    # ================================================================

    def test_add_client_to_channel(self):
        """Test adding client to channel."""
        self.reporter.info("Testing add client to channel", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        client = manager.add_client(
            websocket=ws,
            channel_name="user.123",
            user_id="123",
            wallet_address="test_wallet",
        )

        assert isinstance(client, Client)
        assert client.channel_name == "user.123"
        assert client.user_id == "123"
        assert client.wallet_address == "test_wallet"
        assert "user.123" in manager.channels
        assert ws in manager.channels["user.123"]
        self.reporter.info("Client added successfully", context="Test")

    def test_add_unauthenticated_client(self):
        """Test adding unauthenticated client (no user_id)."""
        self.reporter.info("Testing add unauthenticated client", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        client = manager.add_client(websocket=ws, channel_name="global")

        assert client.user_id is None
        assert client.wallet_address is None
        assert client.channel_name == "global"
        self.reporter.info("Unauthenticated client added", context="Test")

    def test_add_multiple_clients_to_same_channel(self):
        """Test adding multiple clients to same channel."""
        self.reporter.info("Testing multiple clients same channel", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()

        manager.add_client(ws1, "global", "user1")
        manager.add_client(ws2, "global", "user2")
        manager.add_client(ws3, "global", "user3")

        assert len(manager.channels["global"]) == 3
        assert ws1 in manager.channels["global"]
        assert ws2 in manager.channels["global"]
        assert ws3 in manager.channels["global"]
        self.reporter.info("Multiple clients added to channel", context="Test")

    def test_add_client_to_multiple_channels(self):
        """Test adding same client to multiple channels."""
        self.reporter.info("Testing client in multiple channels", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        manager.add_client(ws, "global")
        manager.add_client(ws, "user.123", "123")

        assert ws in manager.channels["global"]
        assert ws in manager.channels["user.123"]
        assert len(manager.channels) == 2
        self.reporter.info("Client added to multiple channels", context="Test")

    def test_add_client_validates_channel_name(self):
        """Test adding client validates channel name."""
        self.reporter.info("Testing channel name validation", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        try:
            manager.add_client(ws, "")
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Invalid channel name rejected", context="Test")

    def test_remove_client_from_channel(self):
        """Test removing client from channel."""
        self.reporter.info("Testing remove client from channel", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        manager.add_client(ws, "user.123", "123")
        assert ws in manager.channels["user.123"]

        manager.remove_client(ws, "user.123")

        assert ws not in manager.channels.get("user.123", [])
        assert id(ws) not in manager.client_registry
        self.reporter.info("Client removed successfully", context="Test")

    def test_remove_nonexistent_client(self):
        """Test removing client that doesn't exist."""
        self.reporter.info("Testing remove nonexistent client", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        # Should not raise error
        manager.remove_client(ws, "user.123")

        self.reporter.info("Nonexistent client removal handled", context="Test")

    def test_remove_client_from_wrong_channel(self):
        """Test removing client from wrong channel."""
        self.reporter.info("Testing remove from wrong channel", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        manager.add_client(ws, "user.123", "123")
        manager.remove_client(ws, "user.456")

        # Client should still be in original channel
        assert ws in manager.channels["user.123"]
        self.reporter.info("Remove from wrong channel handled", context="Test")

    # ================================================================
    # Channel query tests
    # ================================================================

    def test_get_channel_subscribers(self):
        """Test getting channel subscribers."""
        self.reporter.info("Testing get channel subscribers", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()

        manager.add_client(ws1, "global")
        manager.add_client(ws2, "global")

        subscribers = manager.get_channel_subscribers("global")

        assert len(subscribers) == 2
        assert ws1 in subscribers
        assert ws2 in subscribers
        self.reporter.info("Channel subscribers retrieved", context="Test")

    def test_get_subscribers_nonexistent_channel(self):
        """Test getting subscribers for nonexistent channel."""
        self.reporter.info("Testing get nonexistent channel subscribers", context="Test")

        manager = ConnectionManager()

        subscribers = manager.get_channel_subscribers("nonexistent")

        assert subscribers == []
        self.reporter.info("Empty list returned for nonexistent", context="Test")

    def test_get_client(self):
        """Test getting client entity by WebSocket."""
        self.reporter.info("Testing get client entity", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        original_client = manager.add_client(ws, "user.123", "123", "wallet")
        retrieved_client = manager.get_client(ws)

        assert retrieved_client is not None
        assert retrieved_client.user_id == original_client.user_id
        assert retrieved_client.channel_name == original_client.channel_name
        self.reporter.info("Client entity retrieved", context="Test")

    def test_get_client_nonexistent(self):
        """Test getting nonexistent client."""
        self.reporter.info("Testing get nonexistent client", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        client = manager.get_client(ws)

        assert client is None
        self.reporter.info("None returned for nonexistent client", context="Test")

    def test_get_total_connections(self):
        """Test getting total connection count."""
        self.reporter.info("Testing get total connections", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()

        manager.add_client(ws1, "global")
        manager.add_client(ws2, "user.123")
        manager.add_client(ws3, "user.456")

        total = manager.get_total_connections()

        assert total == 3
        self.reporter.info("Total connections correct", context="Test")

    def test_get_channel_count(self):
        """Test getting subscriber count for specific channel."""
        self.reporter.info("Testing get channel count", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()

        manager.add_client(ws1, "global")
        manager.add_client(ws2, "global")

        count = manager.get_channel_count("global")

        assert count == 2
        self.reporter.info("Channel count correct", context="Test")

    def test_get_all_channels(self):
        """Test getting all channels with counts."""
        self.reporter.info("Testing get all channels", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()

        manager.add_client(ws1, "global")
        manager.add_client(ws2, "global")
        manager.add_client(ws3, "user.123")

        channels = manager.get_all_channels()

        assert channels == {"global": 2, "user.123": 1}
        self.reporter.info("All channels retrieved", context="Test")

    def test_channel_exists(self):
        """Test checking if channel exists."""
        self.reporter.info("Testing channel exists check", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        manager.add_client(ws, "global")

        assert manager.channel_exists("global") is True
        assert manager.channel_exists("nonexistent") is False
        self.reporter.info("Channel exists check works", context="Test")

    # ================================================================
    # Channel cleanup tests
    # ================================================================

    def test_cleanup_empty_channels(self):
        """Test cleaning up channels with no subscribers."""
        self.reporter.info("Testing cleanup empty channels", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()

        manager.add_client(ws1, "global")
        manager.add_client(ws2, "user.123")

        # Remove all clients from user.123
        manager.remove_client(ws2, "user.123")

        # Cleanup
        removed = manager.cleanup_empty_channels()

        assert "user.123" in removed
        assert "global" not in removed
        assert manager.channel_exists("user.123") is False
        assert manager.channel_exists("global") is True
        self.reporter.info("Empty channels cleaned up", context="Test")

    def test_cleanup_no_empty_channels(self):
        """Test cleanup when no channels are empty."""
        self.reporter.info("Testing cleanup with no empty channels", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        manager.add_client(ws, "global")

        removed = manager.cleanup_empty_channels()

        assert removed == []
        assert manager.channel_exists("global") is True
        self.reporter.info("No channels removed", context="Test")

    # ================================================================
    # Integration scenarios
    # ================================================================

    def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        self.reporter.info("Testing full connection lifecycle", context="Test")

        manager = ConnectionManager()
        ws = self._create_mock_websocket()

        # Connect
        client = manager.add_client(ws, "user.123", "123", "wallet")
        assert manager.get_total_connections() == 1

        # Verify
        retrieved = manager.get_client(ws)
        assert retrieved.user_id == "123"

        # Query
        assert manager.channel_exists("user.123")
        assert manager.get_channel_count("user.123") == 1

        # Disconnect
        manager.remove_client(ws, "user.123")
        assert manager.get_total_connections() == 0

        # Cleanup
        removed = manager.cleanup_empty_channels()
        assert "user.123" in removed

        self.reporter.info("Full lifecycle completed", context="Test")

    def test_multiple_clients_lifecycle(self):
        """Test lifecycle with multiple clients."""
        self.reporter.info("Testing multiple clients lifecycle", context="Test")

        manager = ConnectionManager()
        ws1 = self._create_mock_websocket()
        ws2 = self._create_mock_websocket()
        ws3 = self._create_mock_websocket()

        # All join global
        manager.add_client(ws1, "global", "user1")
        manager.add_client(ws2, "global", "user2")
        manager.add_client(ws3, "global", "user3")

        assert manager.get_channel_count("global") == 3

        # One leaves
        manager.remove_client(ws2, "global")
        assert manager.get_channel_count("global") == 2

        # Two more join
        ws4 = self._create_mock_websocket()
        ws5 = self._create_mock_websocket()
        manager.add_client(ws4, "global", "user4")
        manager.add_client(ws5, "global", "user5")

        assert manager.get_channel_count("global") == 4
        assert manager.get_total_connections() == 4

        self.reporter.info("Multiple clients lifecycle completed", context="Test")


if __name__ == "__main__":
    TestConnectionManager.run_as_main()
