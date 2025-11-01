"""
WebSocket connection manager infrastructure with production logging.
"""

from typing import Dict, List, Optional

from fastapi import WebSocket
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji

from courier.domain.entities import Client
from courier.domain.value_objects import ChannelName


class ConnectionLimitExceeded(Exception):
    """Raised when connection limit is exceeded."""

    def __init__(self, message: str, limit_type: str):
        """
        Initialize exception.

        Args:
            message: Error message
            limit_type: Type of limit exceeded (global, per_user, per_channel)
        """
        super().__init__(message)
        self.limit_type = limit_type


class ConnectionManager:
    """
    Manages WebSocket connections and channel subscriptions.

    Handles connection lifecycle, client metadata, channel routing,
    and connection limit enforcement.

    Attributes:
        channels: Mapping of channel names to WebSocket connections
        client_registry: Mapping of WebSocket IDs to Client entities
        max_total_connections: Global connection limit (0 = unlimited)
        max_connections_per_user: Per-user connection limit (0 = unlimited)
        max_clients_per_channel: Per-channel connection limit (0 = unlimited)
        reporter: Optional SystemReporter for logging
    """

    def __init__(
        self,
        max_total_connections: int = 0,
        max_connections_per_user: int = 0,
        max_clients_per_channel: int = 0,
        reporter: Optional[SystemReporter] = None,
    ):
        """
        Initialize connection manager.

        Args:
            max_total_connections: Global limit (0 = unlimited)
            max_connections_per_user: Per-user limit (0 = unlimited)
            max_clients_per_channel: Per-channel limit (0 = unlimited)
            reporter: Optional SystemReporter for logging
        """
        self.channels: Dict[str, List[WebSocket]] = {}
        self.client_registry: Dict[int, Client] = {}

        # Connection limits
        self.max_total_connections = max_total_connections
        self.max_connections_per_user = max_connections_per_user
        self.max_clients_per_channel = max_clients_per_channel

        # Reporter for logging
        self.reporter = reporter

        # Log initialization
        if self.reporter:
            self.reporter.info(
                f"ConnectionManager initialized (limits: total={max_total_connections}, "
                f"per_user={max_connections_per_user}, per_channel={max_clients_per_channel})",
                context="ConnectionManager",
                verbose_level=2,
            )

    def check_connection_limits(
        self,
        channel_name: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Check if new connection would exceed limits.

        Args:
            channel_name: Channel to subscribe to
            user_id: Optional authenticated user ID

        Raises:
            ConnectionLimitExceeded: If any limit would be exceeded
        """
        # Check global limit
        if self.max_total_connections > 0:
            total = self.get_total_connections()
            if total >= self.max_total_connections:
                if self.reporter:
                    self.reporter.warning(
                        f"{Emoji.ERROR} Global connection limit exceeded",
                        context="ConnectionManager",
                        current_connections=total,
                        limit=self.max_total_connections,
                        channel=channel_name,
                        user_id=user_id,
                        verbose_level=1,
                    )
                raise ConnectionLimitExceeded(
                    f"Global connection limit reached: {self.max_total_connections}",
                    limit_type="global",
                )

        # Check per-user limit
        if user_id and self.max_connections_per_user > 0:
            user_count = self.get_user_connection_count(user_id)
            if user_count >= self.max_connections_per_user:
                if self.reporter:
                    self.reporter.warning(
                        f"{Emoji.ERROR} Per-user connection limit exceeded",
                        context="ConnectionManager",
                        user_id=user_id,
                        current_connections=user_count,
                        limit=self.max_connections_per_user,
                        channel=channel_name,
                        verbose_level=1,
                    )
                raise ConnectionLimitExceeded(
                    f"User connection limit reached: {self.max_connections_per_user}",
                    limit_type="per_user",
                )

        # Check per-channel limit
        if self.max_clients_per_channel > 0:
            channel_count = self.get_channel_count(channel_name)
            if channel_count >= self.max_clients_per_channel:
                if self.reporter:
                    self.reporter.warning(
                        f"{Emoji.ERROR} Per-channel connection limit exceeded",
                        context="ConnectionManager",
                        channel=channel_name,
                        current_connections=channel_count,
                        limit=self.max_clients_per_channel,
                        user_id=user_id,
                        verbose_level=1,
                    )
                raise ConnectionLimitExceeded(
                    f"Channel connection limit reached: {self.max_clients_per_channel}",
                    limit_type="per_channel",
                )

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

        Raises:
            ConnectionLimitExceeded: If connection limits are exceeded
        """
        # Check limits before adding
        self.check_connection_limits(channel_name, user_id)

        # Validate channel name
        validated_channel = ChannelName(channel_name)

        # Create client entity
        client = Client(
            channel_name=validated_channel.value,
            user_id=user_id,
            wallet_address=wallet_address,
        )

        # Check if channel is new
        is_new_channel = channel_name not in self.channels

        # Add to channel
        if channel_name not in self.channels:
            self.channels[channel_name] = []

        self.channels[channel_name].append(websocket)

        # Register client
        ws_id = id(websocket)
        self.client_registry[ws_id] = client

        # Log client addition
        if self.reporter:
            total_connections = self.get_total_connections()
            channel_count = self.get_channel_count(channel_name)
            user_connections = (
                self.get_user_connection_count(user_id) if user_id else None
            )

            self.reporter.info(
                f"{Emoji.NETWORK.CONNECTED} Client added to channel",
                context="ConnectionManager",
                client_id=client.client_id,
                channel=channel_name,
                user_id=user_id,
                wallet_address=wallet_address,
                is_new_channel=is_new_channel,
                channel_subscribers=channel_count,
                total_connections=total_connections,
                user_connections=user_connections,
                verbose_level=2,
            )

        return client

    def remove_client(self, websocket: WebSocket, channel_name: str) -> None:
        """
        Remove client from channel.

        Args:
            websocket: WebSocket connection
            channel_name: Channel to unsubscribe from
        """
        # Get client info before removal for logging
        ws_id = id(websocket)
        client = self.client_registry.get(ws_id)

        # Remove from channel
        removed_from_channel = False
        if channel_name in self.channels:
            if websocket in self.channels[channel_name]:
                self.channels[channel_name].remove(websocket)
                removed_from_channel = True

        # Remove from registry
        removed_from_registry = False
        if ws_id in self.client_registry:
            del self.client_registry[ws_id]
            removed_from_registry = True

        # Log client removal
        if self.reporter and (removed_from_channel or removed_from_registry):
            total_connections = self.get_total_connections()
            channel_count = self.get_channel_count(channel_name)

            log_context = {
                "context": "ConnectionManager",
                "channel": channel_name,
                "channel_subscribers": channel_count,
                "total_connections": total_connections,
                "verbose_level": 2,
            }

            if client:
                log_context.update(
                    {
                        "client_id": client.client_id,
                        "user_id": client.user_id,
                    }
                )

            self.reporter.info(
                f"{Emoji.NETWORK.DISCONNECT} Client removed from channel",
                **log_context,
            )

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

    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get total connection count for specific user.

        Args:
            user_id: User ID

        Returns:
            Number of connections for user
        """
        count = 0
        for client in self.client_registry.values():
            if client.user_id == user_id:
                count += 1
        return count

    def get_all_channels(self) -> Dict[str, int]:
        """
        Get all channels with subscriber counts.

        Returns:
            Dictionary mapping channel names to subscriber counts
        """
        return {
            channel: len(subscribers) for channel, subscribers in self.channels.items()
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

        # Log cleanup
        if self.reporter and empty_channels:
            self.reporter.info(
                f"{Emoji.SYSTEM.CLEANUP} Empty channels cleaned up",
                context="ConnectionManager",
                channels_removed=len(empty_channels),
                channel_names=empty_channels,
                remaining_channels=len(self.channels),
                verbose_level=2,
            )

        return empty_channels
