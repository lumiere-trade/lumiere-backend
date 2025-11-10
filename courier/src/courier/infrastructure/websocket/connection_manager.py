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
        super().__init__(message)
        self.limit_type = limit_type


class ConnectionManager:
    """Manages WebSocket connections and channel subscriptions."""

    def __init__(
        self,
        max_total_connections: int = 0,
        max_connections_per_user: int = 0,
        max_clients_per_channel: int = 0,
        reporter: Optional[SystemReporter] = None,
    ):
        self.channels: Dict[str, List[WebSocket]] = {}
        self.client_registry: Dict[int, Client] = {}
        self.max_total_connections = max_total_connections
        self.max_connections_per_user = max_connections_per_user
        self.max_clients_per_channel = max_clients_per_channel
        self.reporter = reporter

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
        """Check if new connection would exceed limits."""
        # Check global limit
        if self.max_total_connections > 0:
            total = self.get_total_connections()
            if total >= self.max_total_connections:
                if self.reporter:
                    self.reporter.warning(
                        f"{Emoji.ERROR} Global connection limit exceeded "
                        f"(current={total}, limit={self.max_total_connections}, "
                        f"channel={channel_name}, user={user_id})",
                        context="ConnectionManager",
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
                        f"{Emoji.ERROR} Per-user connection limit exceeded "
                        f"(user={user_id}, current={user_count}, "
                        f"limit={self.max_connections_per_user}, channel={channel_name})",
                        context="ConnectionManager",
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
                        f"{Emoji.ERROR} Per-channel connection limit exceeded "
                        f"(channel={channel_name}, current={channel_count}, "
                        f"limit={self.max_clients_per_channel}, user={user_id})",
                        context="ConnectionManager",
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
        """Add client to channel."""
        # Check limits
        self.check_connection_limits(channel_name, user_id)

        # Validate channel name
        validated_channel = ChannelName(channel_name)

        # Create client entity
        client = Client(
            channel_name=validated_channel.value,
            user_id=user_id,
            wallet_address=wallet_address,
        )

        # Add to channel
        is_new_channel = channel_name not in self.channels
        if channel_name not in self.channels:
            self.channels[channel_name] = []
        self.channels[channel_name].append(websocket)

        # Register client
        ws_id = id(websocket)
        self.client_registry[ws_id] = client

        # Log
        if self.reporter:
            total = self.get_total_connections()
            ch_count = self.get_channel_count(channel_name)
            user_conns = self.get_user_connection_count(user_id) if user_id else 0

            self.reporter.info(
                f"{Emoji.NETWORK.CONNECTED} Client added: channel={channel_name}, "
                f"client={client.id}, user={user_id}, wallet={wallet_address}, "
                f"new_channel={is_new_channel}, channel_subs={ch_count}, "
                f"total={total}, user_conns={user_conns}",
                context="ConnectionManager",
                verbose_level=2,
            )

        return client

    def remove_client(self, websocket: WebSocket, channel_name: str) -> None:
        """Remove client from channel."""
        ws_id = id(websocket)
        client = self.client_registry.get(ws_id)

        # Remove from channel
        if channel_name in self.channels and websocket in self.channels[channel_name]:
            self.channels[channel_name].remove(websocket)

        # Remove from registry
        if ws_id in self.client_registry:
            del self.client_registry[ws_id]

        # Log
        if self.reporter and client:
            total = self.get_total_connections()
            ch_count = self.get_channel_count(channel_name)

            self.reporter.info(
                f"{Emoji.NETWORK.DISCONNECT} Client removed: channel={channel_name}, "
                f"client={client.id}, user={client.user_id}, "
                f"channel_subs={ch_count}, total={total}",
                context="ConnectionManager",
                verbose_level=2,
            )

    def get_channel_subscribers(self, channel_name: str) -> List[WebSocket]:
        """Get all subscribers for a channel."""
        return self.channels.get(channel_name, [])

    def get_client(self, websocket: WebSocket) -> Optional[Client]:
        """Get client entity for WebSocket connection."""
        ws_id = id(websocket)
        return self.client_registry.get(ws_id)

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(subs) for subs in self.channels.values())

    def get_channel_count(self, channel_name: str) -> int:
        """Get subscriber count for specific channel."""
        return len(self.channels.get(channel_name, []))

    def get_user_connection_count(self, user_id: str) -> int:
        """Get total connection count for specific user."""
        return sum(1 for c in self.client_registry.values() if c.user_id == user_id)

    def get_all_channels(self) -> Dict[str, int]:
        """Get all channels with subscriber counts."""
        return {ch: len(subs) for ch, subs in self.channels.items()}

    def channel_exists(self, channel_name: str) -> bool:
        """Check if channel exists."""
        return channel_name in self.channels

    def cleanup_empty_channels(self) -> List[str]:
        """Remove channels with no subscribers."""
        empty = [ch for ch, subs in self.channels.items() if len(subs) == 0]
        for ch in empty:
            del self.channels[ch]

        if self.reporter and empty:
            self.reporter.info(
                f"{Emoji.SYSTEM.CLEANUP} Empty channels cleaned: "
                f"removed={len(empty)}, names={empty}, remaining={len(self.channels)}",
                context="ConnectionManager",
                verbose_level=2,
            )

        return empty
