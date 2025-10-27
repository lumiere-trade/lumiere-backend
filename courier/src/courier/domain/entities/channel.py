"""
Channel entity - represents a message channel.
"""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4


class Channel:
    """
    Channel entity representing a message broadcasting channel.

    A channel is a logical grouping for message distribution.
    Clients subscribe to channels to receive messages.

    Attributes:
        id: Unique channel identifier
        name: Channel name (e.g., 'global', 'user.123')
        created_at: Channel creation timestamp
        is_ephemeral: Whether channel auto-deletes when empty
    """

    def __init__(
        self,
        name: str,
        is_ephemeral: bool = False,
        channel_id: UUID = None,
        created_at: datetime = None,
    ):
        """
        Initialize Channel entity.

        Args:
            name: Channel name
            is_ephemeral: Auto-delete when empty
            channel_id: Optional channel ID (generated if not provided)
            created_at: Optional creation timestamp
        """
        self.id: UUID = channel_id or uuid4()
        self.name: str = name
        self.is_ephemeral: bool = is_ephemeral
        self.created_at: datetime = created_at or datetime.utcnow()

    def __eq__(self, other) -> bool:
        """Check equality based on channel ID."""
        if not isinstance(other, Channel):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on channel ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Channel(id={self.id}, name={self.name}, "
            f"ephemeral={self.is_ephemeral})"
        )
