"""
Client entity - represents a connected WebSocket client.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class Client:
    """
    Client entity representing a WebSocket connection.

    A client is a connected user subscribed to one or more channels.

    Attributes:
        id: Unique client identifier
        user_id: Authenticated user ID (optional)
        wallet_address: User's wallet address (optional)
        channel_name: Subscribed channel name
        connected_at: Connection timestamp
    """

    def __init__(
        self,
        channel_name: str,
        user_id: Optional[str] = None,
        wallet_address: Optional[str] = None,
        client_id: UUID = None,
        connected_at: datetime = None,
    ):
        """
        Initialize Client entity.

        Args:
            channel_name: Channel the client is subscribed to
            user_id: Optional authenticated user ID
            wallet_address: Optional wallet address
            client_id: Optional client ID (generated if not provided)
            connected_at: Optional connection timestamp
        """
        self.id: UUID = client_id or uuid4()
        self.user_id: Optional[str] = user_id
        self.wallet_address: Optional[str] = wallet_address
        self.channel_name: str = channel_name
        self.connected_at: datetime = connected_at or datetime.utcnow()

    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.user_id is not None

    def __eq__(self, other) -> bool:
        """Check equality based on client ID."""
        if not isinstance(other, Client):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on client ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        auth = f"user_id={self.user_id}" if self.user_id else "unauthenticated"
        return f"Client(id={self.id}, channel={self.channel_name}, {auth})"
