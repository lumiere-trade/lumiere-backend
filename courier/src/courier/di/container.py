"""
Dependency Injection container for Courier.

Manages lifecycle and dependencies of all application components.
"""

from datetime import datetime
from typing import Optional

from courier.application.use_cases import (
    AuthenticateWebSocketUseCase,
    BroadcastMessageUseCase,
    ManageChannelUseCase,
)
from courier.config.settings import Settings
from courier.infrastructure.auth import JWTVerifier
from courier.infrastructure.websocket import ConnectionManager


class Container:
    """
    Dependency Injection container.

    Creates and manages all application dependencies.
    Implements singleton pattern for shared resources.
    """

    def __init__(self, settings: Settings):
        """
        Initialize container with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Shared infrastructure
        self._connection_manager: Optional[ConnectionManager] = None
        self._jwt_verifier: Optional[JWTVerifier] = None

        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "start_time": datetime.utcnow(),
        }

    @property
    def connection_manager(self) -> ConnectionManager:
        """
        Get ConnectionManager singleton.

        Returns:
            ConnectionManager instance
        """
        if self._connection_manager is None:
            self._connection_manager = ConnectionManager()
        return self._connection_manager

    @property
    def jwt_verifier(self) -> Optional[JWTVerifier]:
        """
        Get JWTVerifier singleton.

        Returns:
            JWTVerifier instance if auth enabled, None otherwise
        """
        if not self.settings.require_auth:
            return None

        if self._jwt_verifier is None:
            if not self.settings.jwt_secret:
                raise ValueError(
                    "JWT authentication enabled but jwt_secret not configured"
                )

            self._jwt_verifier = JWTVerifier(
                secret=self.settings.jwt_secret,
                algorithm=self.settings.jwt_algorithm,
            )

        return self._jwt_verifier

    def get_authenticate_use_case(self) -> Optional[AuthenticateWebSocketUseCase]:
        """
        Get AuthenticateWebSocketUseCase.

        Returns:
            Use case instance if auth enabled, None otherwise
        """
        if not self.settings.require_auth:
            return None

        return AuthenticateWebSocketUseCase(self.jwt_verifier)

    def get_broadcast_use_case(self) -> BroadcastMessageUseCase:
        """
        Get BroadcastMessageUseCase.

        Returns:
            Use case instance
        """
        return BroadcastMessageUseCase()

    def get_manage_channel_use_case(self) -> ManageChannelUseCase:
        """
        Get ManageChannelUseCase.

        Returns:
            Use case instance
        """
        return ManageChannelUseCase(self.connection_manager.channels)

    def increment_stat(self, stat_name: str, amount: int = 1) -> None:
        """
        Increment a statistic counter.

        Args:
            stat_name: Name of statistic to increment
            amount: Amount to increment by
        """
        if stat_name in self.stats:
            self.stats[stat_name] += amount

    def get_uptime_seconds(self) -> float:
        """
        Get server uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return (datetime.utcnow() - self.stats["start_time"]).total_seconds()
