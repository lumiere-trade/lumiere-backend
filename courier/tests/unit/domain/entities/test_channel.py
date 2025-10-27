"""
Unit tests for Channel entity.

Tests channel creation, validation, and properties.

Usage:
    python -m courier.tests.unit.domain.entities.test_channel
    laborant courier --unit
"""

from datetime import datetime
from uuid import UUID

from courier.domain.entities.channel import Channel
from shared.tests import LaborantTest


class TestChannel(LaborantTest):
    """Unit tests for Channel entity."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Creation tests
    # ================================================================

    def test_create_channel_with_name(self):
        """Test creating Channel with valid name."""
        self.reporter.info("Testing channel creation", context="Test")

        channel = Channel(name="user.123")

        assert channel.name == "user.123"
        assert isinstance(channel.id, UUID)
        assert isinstance(channel.created_at, datetime)
        assert channel.is_ephemeral is False
        self.reporter.info("Channel created successfully", context="Test")

    def test_channel_auto_generates_id(self):
        """Test Channel auto-generates UUID."""
        self.reporter.info("Testing auto-generated UUID", context="Test")

        channel = Channel(name="global")

        assert isinstance(channel.id, UUID)
        assert channel.id is not None
        self.reporter.info(f"Generated UUID: {channel.id}", context="Test")

    def test_channel_auto_generates_timestamp(self):
        """Test Channel auto-generates created_at timestamp."""
        self.reporter.info("Testing auto-generated timestamp", context="Test")

        channel = Channel(name="strategy.abc")

        assert isinstance(channel.created_at, datetime)
        self.reporter.info("Timestamp auto-generated", context="Test")

    def test_create_ephemeral_channel(self):
        """Test creating ephemeral channel."""
        self.reporter.info("Testing ephemeral channel creation", context="Test")

        channel = Channel(name="forge.job.xyz", is_ephemeral=True)

        assert channel.is_ephemeral is True
        assert channel.name == "forge.job.xyz"
        self.reporter.info("Ephemeral channel created", context="Test")

    def test_create_channel_with_custom_id(self):
        """Test creating Channel with custom UUID."""
        self.reporter.info("Testing channel with custom ID", context="Test")

        from uuid import uuid4
        custom_id = uuid4()
        channel = Channel(name="test", channel_id=custom_id)

        assert channel.id == custom_id
        self.reporter.info("Channel created with custom ID", context="Test")

    def test_create_channel_with_custom_timestamp(self):
        """Test creating Channel with custom timestamp."""
        self.reporter.info("Testing channel with custom timestamp", context="Test")

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        channel = Channel(name="test", created_at=custom_time)

        assert channel.created_at == custom_time
        self.reporter.info("Channel created with custom timestamp", context="Test")

    # ================================================================
    # Equality tests
    # ================================================================

    def test_channels_with_same_id_are_equal(self):
        """Test two Channels with same ID are equal."""
        self.reporter.info("Testing channel equality", context="Test")

        from uuid import uuid4
        channel_id = uuid4()
        channel1 = Channel(name="user.123", channel_id=channel_id)
        channel2 = Channel(name="user.456", channel_id=channel_id)

        assert channel1 == channel2
        self.reporter.info("Channels with same ID are equal", context="Test")

    def test_channels_with_different_ids_not_equal(self):
        """Test two Channels with different IDs are not equal."""
        self.reporter.info("Testing channel inequality", context="Test")

        channel1 = Channel(name="user.123")
        channel2 = Channel(name="user.123")

        assert channel1 != channel2
        self.reporter.info("Channels with different IDs not equal", context="Test")

    def test_channel_not_equal_to_non_channel(self):
        """Test Channel not equal to non-Channel object."""
        self.reporter.info("Testing inequality with non-Channel", context="Test")

        channel = Channel(name="global")

        assert channel != "global"
        assert channel != 123
        assert channel != None
        self.reporter.info("Channel not equal to non-Channel", context="Test")

    # ================================================================
    # Hashing tests
    # ================================================================

    def test_channel_hashable(self):
        """Test Channel can be used in sets and dicts."""
        self.reporter.info("Testing channel hashability", context="Test")

        channel1 = Channel(name="user.123")
        channel2 = Channel(name="user.456")
        channel3 = Channel(name="user.123", channel_id=channel1.id)

        # Test in set
        channel_set = {channel1, channel2, channel3}
        assert len(channel_set) == 2
        self.reporter.info("Channel works in set", context="Test")

        # Test as dict key
        channel_dict = {channel1: "value1", channel2: "value2"}
        assert channel_dict[channel3] == "value1"
        self.reporter.info("Channel works as dict key", context="Test")

    # ================================================================
    # String representation tests
    # ================================================================

    def test_channel_repr(self):
        """Test Channel string representation."""
        self.reporter.info("Testing channel repr", context="Test")

        channel = Channel(name="user.123", is_ephemeral=True)
        repr_str = repr(channel)

        assert "Channel" in repr_str
        assert "user.123" in repr_str
        assert "ephemeral=True" in repr_str
        assert str(channel.id) in repr_str
        self.reporter.info(f"Channel repr: {repr_str}", context="Test")

    # ================================================================
    # Edge cases
    # ================================================================

    def test_two_channels_different_ids(self):
        """Test two channels have different IDs."""
        self.reporter.info("Testing two channels have different IDs", context="Test")

        channel1 = Channel(name="user.123")
        channel2 = Channel(name="user.123")

        assert channel1.id != channel2.id
        self.reporter.info("Different channels have different IDs", context="Test")

    def test_channel_attributes_mutable(self):
        """Test Channel attributes are mutable."""
        self.reporter.info("Testing channel mutability", context="Test")

        channel = Channel(name="user.123")
        
        # Name is mutable
        channel.name = "user.456"
        assert channel.name == "user.456"

        # Ephemeral flag is mutable
        channel.is_ephemeral = True
        assert channel.is_ephemeral is True

        self.reporter.info("Channel attributes are mutable", context="Test")


if __name__ == "__main__":
    TestChannel.run_as_main()
