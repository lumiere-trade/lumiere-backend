"""
Unit tests for ManageChannelUseCase.

Tests channel lifecycle management including creation, retrieval, and cleanup.

Usage:
    python -m courier.tests.unit.application.use_cases.test_manage_channel
    laborant courier --unit
"""

from unittest.mock import Mock

from shared.tests import LaborantTest

from courier.application.use_cases.manage_channel import ManageChannelUseCase
from courier.domain.entities import Channel


class TestManageChannelUseCase(LaborantTest):
    """Unit tests for ManageChannelUseCase."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # create_or_get_channel tests
    # ================================================================

    def test_create_new_channel(self):
        """Test creating a new channel."""
        self.reporter.info("Testing new channel creation", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        channel = use_case.create_or_get_channel("user.123")

        assert channel.name == "user.123"
        assert isinstance(channel, Channel)
        assert "user.123" in channels
        assert channels["user.123"] == []
        self.reporter.info("New channel created successfully", context="Test")

    def test_create_ephemeral_channel(self):
        """Test creating an ephemeral channel."""
        self.reporter.info("Testing ephemeral channel creation", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        channel = use_case.create_or_get_channel("forge.job.xyz")

        assert channel.name == "forge.job.xyz"
        assert channel.is_ephemeral is True
        assert "forge.job.xyz" in channels
        self.reporter.info("Ephemeral channel created", context="Test")

    def test_create_persistent_channel(self):
        """Test creating a persistent channel."""
        self.reporter.info("Testing persistent channel creation", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        channel = use_case.create_or_get_channel("global")

        assert channel.name == "global"
        assert channel.is_ephemeral is False
        self.reporter.info("Persistent channel created", context="Test")

    def test_get_existing_channel(self):
        """Test getting an existing channel."""
        self.reporter.info("Testing existing channel retrieval", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        # Create channel first
        channel1 = use_case.create_or_get_channel("strategy.abc")

        # Get same channel
        channel2 = use_case.create_or_get_channel("strategy.abc")

        assert channel2.name == "strategy.abc"
        assert channel1.name == channel2.name
        self.reporter.info("Existing channel retrieved", context="Test")

    def test_create_channel_initializes_empty_subscriber_list(self):
        """Test new channel has empty subscriber list."""
        self.reporter.info("Testing empty subscriber list init", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("user.456")

        assert "user.456" in channels
        assert isinstance(channels["user.456"], list)
        assert len(channels["user.456"]) == 0
        self.reporter.info("Subscriber list initialized empty", context="Test")

    def test_create_channel_with_invalid_name(self):
        """Test creating channel with invalid name raises error."""
        self.reporter.info("Testing invalid channel name", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        try:
            use_case.create_or_get_channel("")
            assert False, "Should have raised ValueError"
        except ValueError:
            self.reporter.info("Invalid channel name rejected", context="Test")

    def test_create_multiple_channels(self):
        """Test creating multiple different channels."""
        self.reporter.info("Testing multiple channel creation", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("user.123")
        use_case.create_or_get_channel("strategy.abc")
        use_case.create_or_get_channel("global")

        assert len(channels) == 3
        assert "user.123" in channels
        assert "strategy.abc" in channels
        assert "global" in channels
        self.reporter.info("Multiple channels created", context="Test")

    # ================================================================
    # get_subscriber_count tests
    # ================================================================

    def test_get_subscriber_count_empty_channel(self):
        """Test getting subscriber count for empty channel."""
        self.reporter.info("Testing subscriber count for empty channel", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("user.123")
        count = use_case.get_subscriber_count("user.123")

        assert count == 0
        self.reporter.info("Empty channel has 0 subscribers", context="Test")

    def test_get_subscriber_count_with_subscribers(self):
        """Test getting subscriber count with subscribers."""
        self.reporter.info("Testing subscriber count with subscribers", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("global")

        # Add mock subscribers
        mock_ws1 = Mock()
        mock_ws2 = Mock()
        mock_ws3 = Mock()
        channels["global"].extend([mock_ws1, mock_ws2, mock_ws3])

        count = use_case.get_subscriber_count("global")

        assert count == 3
        self.reporter.info("Correct subscriber count returned", context="Test")

    def test_get_subscriber_count_nonexistent_channel(self):
        """Test getting subscriber count for nonexistent channel."""
        self.reporter.info(
            "Testing subscriber count for nonexistent channel", context="Test"
        )

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        count = use_case.get_subscriber_count("nonexistent")

        assert count == 0
        self.reporter.info("Nonexistent channel returns 0", context="Test")

    # ================================================================
    # should_cleanup_channel tests
    # ================================================================

    def test_should_cleanup_ephemeral_channel_no_subscribers(self):
        """Test ephemeral channel with no subscribers should be cleaned up."""
        self.reporter.info("Testing cleanup of empty ephemeral channel", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("forge.job.xyz")

        should_cleanup = use_case.should_cleanup_channel("forge.job.xyz")

        assert should_cleanup is True
        self.reporter.info("Empty ephemeral channel should cleanup", context="Test")

    def test_should_not_cleanup_ephemeral_channel_with_subscribers(self):
        """Test ephemeral channel with subscribers should not be cleaned up."""
        self.reporter.info(
            "Testing cleanup of ephemeral with subscribers", context="Test"
        )

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("forge.job.xyz")
        mock_ws = Mock()
        channels["forge.job.xyz"].append(mock_ws)

        should_cleanup = use_case.should_cleanup_channel("forge.job.xyz")

        assert should_cleanup is False
        self.reporter.info(
            "Ephemeral with subscribers should not cleanup", context="Test"
        )

    def test_should_not_cleanup_persistent_channel_no_subscribers(self):
        """Test persistent channel should never be cleaned up."""
        self.reporter.info(
            "Testing cleanup of empty persistent channel", context="Test"
        )

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("global")

        should_cleanup = use_case.should_cleanup_channel("global")

        assert should_cleanup is False
        self.reporter.info("Persistent channel should not cleanup", context="Test")

    def test_should_not_cleanup_persistent_channel_with_subscribers(self):
        """Test persistent channel with subscribers should not be cleaned up."""
        self.reporter.info(
            "Testing cleanup of persistent with subscribers", context="Test"
        )

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        use_case.create_or_get_channel("user.123")
        mock_ws = Mock()
        channels["user.123"].append(mock_ws)

        should_cleanup = use_case.should_cleanup_channel("user.123")

        assert should_cleanup is False
        self.reporter.info(
            "Persistent with subscribers should not cleanup", context="Test"
        )

    def test_should_cleanup_invalid_channel_name(self):
        """Test invalid channel name should be cleaned up."""
        self.reporter.info("Testing cleanup of invalid channel name", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        should_cleanup = use_case.should_cleanup_channel("")

        assert should_cleanup is True
        self.reporter.info("Invalid channel name should cleanup", context="Test")

    def test_should_cleanup_nonexistent_channel(self):
        """Test nonexistent ephemeral channel should cleanup."""
        self.reporter.info("Testing cleanup of nonexistent channel", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        should_cleanup = use_case.should_cleanup_channel("backtest.test")

        assert should_cleanup is True
        self.reporter.info("Nonexistent ephemeral should cleanup", context="Test")

    # ================================================================
    # Integration tests
    # ================================================================

    def test_full_channel_lifecycle(self):
        """Test complete channel lifecycle."""
        self.reporter.info("Testing full channel lifecycle", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        # Create channel
        channel = use_case.create_or_get_channel("forge.job.test")
        assert channel.is_ephemeral is True

        # Check subscriber count
        assert use_case.get_subscriber_count("forge.job.test") == 0

        # Should cleanup (no subscribers)
        assert use_case.should_cleanup_channel("forge.job.test") is True

        # Add subscriber
        mock_ws = Mock()
        channels["forge.job.test"].append(mock_ws)

        # Should not cleanup (has subscriber)
        assert use_case.should_cleanup_channel("forge.job.test") is False

        # Remove subscriber
        channels["forge.job.test"].remove(mock_ws)

        # Should cleanup again
        assert use_case.should_cleanup_channel("forge.job.test") is True

        self.reporter.info("Full lifecycle completed", context="Test")

    def test_multiple_channels_independent(self):
        """Test multiple channels operate independently."""
        self.reporter.info("Testing channel independence", context="Test")

        channels = {}
        use_case = ManageChannelUseCase(channels=channels)

        # Create channels
        use_case.create_or_get_channel("user.123")
        use_case.create_or_get_channel("forge.job.abc")

        # Add subscriber to one
        mock_ws = Mock()
        channels["user.123"].append(mock_ws)

        # Check counts are independent
        assert use_case.get_subscriber_count("user.123") == 1
        assert use_case.get_subscriber_count("forge.job.abc") == 0

        # Check cleanup is independent
        assert use_case.should_cleanup_channel("user.123") is False
        assert use_case.should_cleanup_channel("forge.job.abc") is True

        self.reporter.info("Channels operate independently", context="Test")


if __name__ == "__main__":
    TestManageChannelUseCase.run_as_main()
