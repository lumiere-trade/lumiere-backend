"""
Use case for managing channels.
"""

from typing import Dict, List

from fastapi import WebSocket

from courier.domain.entities import Channel
from courier.domain.value_objects import ChannelName


class ManageChannelUseCase:
    """
    Use case for channel lifecycle management.

    Handles channel creation, retrieval, and cleanup.
    """

    def __init__(self, channels: Dict[str, List[WebSocket]]):
        """
        Initialize use case.

        Args:
            channels: Dictionary mapping channel names to subscriber lists
        """
        self.channels = channels

    def create_or_get_channel(self, channel_name: str) -> Channel:
        """
        Create channel if it doesn't exist, or return existing.

        Args:
            channel_name: Channel name to create/get

        Returns:
            Channel entity

        Raises:
            ValueError: If channel name is invalid
        """
        # Validate channel name
        validated_name = ChannelName(channel_name)

        # Check if channel exists
        if channel_name not in self.channels:
            # Create new channel
            is_ephemeral = validated_name.is_ephemeral()
            channel = Channel(name=channel_name, is_ephemeral=is_ephemeral)

            # Initialize subscriber list
            self.channels[channel_name] = []

            return channel

        # Return existing channel info
        return Channel(
            name=channel_name,
            is_ephemeral=validated_name.is_ephemeral(),
        )

    def get_subscriber_count(self, channel_name: str) -> int:
        """
        Get number of subscribers for a channel.

        Args:
            channel_name: Channel name

        Returns:
            Number of subscribers
        """
        return len(self.channels.get(channel_name, []))

    def should_cleanup_channel(self, channel_name: str) -> bool:
        """
        Check if channel should be cleaned up.

        Ephemeral channels with no subscribers should be removed.

        Args:
            channel_name: Channel name

        Returns:
            True if channel should be cleaned up
        """
        try:
            validated_name = ChannelName(channel_name)

            # Only cleanup ephemeral channels
            if not validated_name.is_ephemeral():
                return False

            # Cleanup if no subscribers
            return self.get_subscriber_count(channel_name) == 0

        except ValueError:
            # Invalid channel name, cleanup
            return True
