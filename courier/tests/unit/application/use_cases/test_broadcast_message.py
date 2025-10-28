"""
Unit tests for BroadcastMessageUseCase.

Tests message broadcasting to channel subscribers.

Usage:
    python -m courier.tests.unit.application.use_cases.test_broadcast_message
    laborant courier --unit
"""

from unittest.mock import AsyncMock, Mock

from shared.tests import LaborantTest

from courier.application.use_cases.broadcast_message import BroadcastMessageUseCase


class TestBroadcastMessageUseCase(LaborantTest):
    """Unit tests for BroadcastMessageUseCase."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Successful broadcast tests
    # ================================================================

    async def test_broadcast_to_single_subscriber(self):
        """Test broadcasting message to single subscriber."""
        self.reporter.info("Testing broadcast to single subscriber", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        message_data = {"type": "trade", "amount": 100}
        sent_count = await use_case.execute("user.123", message_data, subscribers)

        assert sent_count == 1
        mock_ws.send_json.assert_called_once_with(message_data)
        self.reporter.info("Message sent to single subscriber", context="Test")

    async def test_broadcast_to_multiple_subscribers(self):
        """Test broadcasting message to multiple subscribers."""
        self.reporter.info("Testing broadcast to multiple subscribers", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws1 = Mock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_json = AsyncMock()
        mock_ws3 = Mock()
        mock_ws3.send_json = AsyncMock()
        subscribers = [mock_ws1, mock_ws2, mock_ws3]

        message_data = {"type": "notification", "text": "hello"}
        sent_count = await use_case.execute("global", message_data, subscribers)

        assert sent_count == 3
        mock_ws1.send_json.assert_called_once_with(message_data)
        mock_ws2.send_json.assert_called_once_with(message_data)
        mock_ws3.send_json.assert_called_once_with(message_data)
        self.reporter.info("Message sent to all subscribers", context="Test")

    async def test_broadcast_to_empty_subscriber_list(self):
        """Test broadcasting to empty subscriber list."""
        self.reporter.info("Testing broadcast to empty list", context="Test")

        use_case = BroadcastMessageUseCase()
        subscribers = []
        message_data = {"type": "test"}

        sent_count = await use_case.execute("strategy.abc", message_data, subscribers)

        assert sent_count == 0
        self.reporter.info("Broadcast to empty list returns 0", context="Test")

    async def test_broadcast_complex_message(self):
        """Test broadcasting complex nested message."""
        self.reporter.info("Testing broadcast of complex message", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        complex_data = {
            "type": "strategy.update",
            "payload": {
                "id": "abc",
                "status": "active",
                "metrics": {"sharpe": 1.5, "trades": [1, 2, 3]},
            },
        }

        sent_count = await use_case.execute("strategy.abc", complex_data, subscribers)

        assert sent_count == 1
        mock_ws.send_json.assert_called_once_with(complex_data)
        self.reporter.info("Complex message broadcasted successfully", context="Test")

    # ================================================================
    # Dead connection handling tests
    # ================================================================

    async def test_broadcast_with_one_dead_connection(self):
        """Test broadcasting when one connection is dead."""
        self.reporter.info("Testing broadcast with dead connection", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws1 = Mock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        mock_ws3 = Mock()
        mock_ws3.send_json = AsyncMock()
        subscribers = [mock_ws1, mock_ws2, mock_ws3]

        message_data = {"type": "test"}
        sent_count = await use_case.execute("global", message_data, subscribers)

        assert sent_count == 2
        self.reporter.info("Message sent to 2/3 subscribers (1 dead)", context="Test")

    async def test_broadcast_all_connections_dead(self):
        """Test broadcasting when all connections are dead."""
        self.reporter.info("Testing broadcast with all dead connections", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws1 = Mock()
        mock_ws1.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        mock_ws2 = Mock()
        mock_ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        subscribers = [mock_ws1, mock_ws2]

        message_data = {"type": "test"}
        sent_count = await use_case.execute("user.123", message_data, subscribers)

        assert sent_count == 0
        self.reporter.info("No messages sent (all connections dead)", context="Test")

    async def test_broadcast_continues_after_dead_connection(self):
        """Test broadcasting continues after encountering dead connection."""
        self.reporter.info("Testing broadcast continues after error", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws1 = Mock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        mock_ws3 = Mock()
        mock_ws3.send_json = AsyncMock()
        subscribers = [mock_ws1, mock_ws2, mock_ws3]

        message_data = {"type": "test"}
        sent_count = await use_case.execute("global", message_data, subscribers)

        # Both ws1 and ws3 should receive message despite ws2 failing
        assert sent_count == 2
        mock_ws1.send_json.assert_called_once()
        mock_ws3.send_json.assert_called_once()
        self.reporter.info("Broadcast continued after error", context="Test")

    # ================================================================
    # Validation tests
    # ================================================================

    async def test_broadcast_with_invalid_channel_name(self):
        """Test broadcasting with invalid channel name raises error."""
        self.reporter.info("Testing invalid channel name", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        try:
            await use_case.execute("", {"type": "test"}, subscribers)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Invalid channel name rejected", context="Test")

    async def test_broadcast_with_invalid_message_data(self):
        """Test broadcasting with invalid message data raises error."""
        self.reporter.info("Testing invalid message data", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        try:
            await use_case.execute("user.123", {}, subscribers)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Invalid message data rejected", context="Test")

    async def test_broadcast_validates_channel_name_format(self):
        """Test broadcasting validates channel name format."""
        self.reporter.info("Testing channel name format validation", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        try:
            await use_case.execute("INVALID", {"type": "test"}, subscribers)
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Invalid format rejected", context="Test")

    # ================================================================
    # Channel type tests
    # ================================================================

    async def test_broadcast_to_user_channel(self):
        """Test broadcasting to user-specific channel."""
        self.reporter.info("Testing broadcast to user channel", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        sent_count = await use_case.execute(
            "user.123", {"type": "notification"}, subscribers
        )

        assert sent_count == 1
        self.reporter.info("Broadcast to user channel successful", context="Test")

    async def test_broadcast_to_strategy_channel(self):
        """Test broadcasting to strategy-specific channel."""
        self.reporter.info("Testing broadcast to strategy channel", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        sent_count = await use_case.execute(
            "strategy.abc-123", {"type": "update"}, subscribers
        )

        assert sent_count == 1
        self.reporter.info("Broadcast to strategy channel successful", context="Test")

    async def test_broadcast_to_global_channel(self):
        """Test broadcasting to global channel."""
        self.reporter.info("Testing broadcast to global channel", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        sent_count = await use_case.execute("global", {"type": "announcement"}, subscribers)

        assert sent_count == 1
        self.reporter.info("Broadcast to global channel successful", context="Test")

    async def test_broadcast_to_ephemeral_channel(self):
        """Test broadcasting to ephemeral channel."""
        self.reporter.info("Testing broadcast to ephemeral channel", context="Test")

        use_case = BroadcastMessageUseCase()
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        subscribers = [mock_ws]

        sent_count = await use_case.execute("forge.job.xyz", {"type": "progress"}, subscribers)

        assert sent_count == 1
        self.reporter.info("Broadcast to ephemeral channel successful", context="Test")


if __name__ == "__main__":
    TestBroadcastMessageUseCase.run_as_main()
