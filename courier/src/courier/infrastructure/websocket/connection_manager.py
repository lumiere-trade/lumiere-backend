"""
WebSocket connection manager infrastructure.
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import WebSocket

from courier.domain.entities import Client
from courier.domain.value_objects import ChannelName


class ConnectionManager:
    """
    Manages WebSocket connections and channel subscriptions.

    Handles connection lifecycle, client metadata, and channel routing.

    Attributes:
        channels: Mapping of channel names to WebSocket connections
        client_registry: Mapping of WebSocket IDs to Client entities
    """

    def __init__(self):
        """Initialize connection manager."""
        self.channels: Dict[str, List[WebSocket]] = {}
        self.client_registry: Dict[int, Client] = {}

    def add_client(
        self,
        websocket: WebSocket,
        channel_name: str,
        user_id: Optional[str] = None,
        wallet_address: Optional[str] = None,
    ) -> Client:
        """
        Add client to channel.

        Args:
            websocket: WebSocket connection
            channel_name: Channel to subscribe to
            user_id: Optional authenticated user ID
            wallet_address: Optional wallet address

        Returns:
            Created Client entity
        """
        # Validate channel name
        validated_channel = ChannelName(channel_name)

        # Create client entity
        client = Client(
            channel_name=validated_channel.value,
            user_id=user_id,
            wallet_address=wallet_address,
        )

        # Add to channel
        if channel_name not in self.channels:
            self.channels[channel_name] = []

        self.channels[channel_name].append(websocket)

        # Register client
        ws_id = id(websocket)
        self.client_registry[ws_id] = client

        return client

    def remove_client(self, websocket: WebSocket, channel_name: str) -> None:
        """
        Remove client from channel.

        Args:
            websocket: WebSocket connection
            channel_name: Channel to unsubscribe from
        """
        # Remove from channel
        if channel_name in self.channels:
            if websocket in self.channels[channel_name]:
                self.channels[channel_name].remove(websocket)

        # Remove from registry
        ws_id = id(websocket)
        if ws_id in self.client_registry:
            del self.client_registry[ws_id]

    def get_channel_subscribers(self, channel_name: str) -> List[WebSocket]:
        """
        Get all subscribers for a channel.

        Args:
            channel_name: Channel name

        Returns:
            List of WebSocket connections
        """
        return self.channels.get(channel_name, [])

    def get_client(self, websocket: WebSocket) -> Optional[Client]:
        """
        Get client entity for WebSocket connection.

        Args:
            websocket: WebSocket connection

        Returns:
            Client entity or None if not found
        """
        ws_id = id(websocket)
        return self.client_registry.get(ws_id)

    def get_total_connections(self) -> int:
        """
        Get total number of active connections.

        Returns:
            Total connection count
        """
        return sum(len(subs) for subs in self.channels.values())

    def get_channel_count(self, channel_name: str) -> int:
        """
        Get subscriber count for specific channel.

        Args:
            channel_name: Channel name

        Returns:
            Number of subscribers
        """
        return len(self.channels.get(channel_name, []))

    def get_all_channels(self) -> Dict[str, int]:
        """
        Get all channels with subscriber counts.

        Returns:
            Dictionary mapping channel names to subscriber counts
        """
        return {
            channel: len(subscribers)
            for channel, subscribers in self.channels.items()
        }

    def channel_exists(self, channel_name: str) -> bool:
        """
        Check if channel exists.

        Args:
            channel_name: Channel name

        Returns:
            True if channel exists
        """
        return channel_name in self.channels

    def cleanup_empty_channels(self) -> List[str]:
        """
        Remove channels with no subscribers.

        Returns:
            List of removed channel names
        """
        empty_channels = [
            channel
            for channel, subscribers in self.channels.items()
            if len(subscribers) == 0
        ]

        for channel in empty_channels:
            del self.channels[channel]

        return empty_channels
