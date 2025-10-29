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
    ValidateEventUseCase,
    ValidateMessageUseCase,
)
from courier.config.settings import Settings
from courier.infrastructure.auth import JWTVerifier
from courier.infrastructure.rate_limiting import RateLimiter
from courier.infrastructure.shutdown import ShutdownManager
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
        self._validate_event_use_case: Optional[ValidateEventUseCase] = None
        self._validate_message_use_case: Optional[ValidateMessageUseCase] = None
        self._shutdown_manager: Optional[ShutdownManager] = None

        # Rate limiters
        self._publish_rate_limiter: Optional[RateLimiter] = None
        self._websocket_rate_limiter: Optional[RateLimiter] = None

        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "rate_limit_hits": 0,
            "validation_failures": 0,
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

    @property
    def shutdown_manager(self) -> ShutdownManager:
        """
        Get ShutdownManager singleton.

        Returns:
            ShutdownManager instance
        """
        if self._shutdown_manager is None:
            self._shutdown_manager = ShutdownManager(
                shutdown_timeout=self.settings.shutdown_timeout,
                grace_period=self.settings.shutdown_grace_period,
            )
        return self._shutdown_manager

    @property
    def publish_rate_limiter(self) -> Optional[RateLimiter]:
        """
        Get publish rate limiter singleton.

        Returns:
            RateLimiter instance if rate limiting enabled, None otherwise
        """
        if not self.settings.rate_limit_enabled:
            return None

        if self._publish_rate_limiter is None:
            self._publish_rate_limiter = RateLimiter(
                limit=self.settings.rate_limit_publish_requests,
                window_seconds=self.settings.rate_limit_window_seconds,
            )

        return self._publish_rate_limiter

    @property
    def websocket_rate_limiter(self) -> Optional[RateLimiter]:
        """
        Get WebSocket rate limiter singleton.

        Returns:
            RateLimiter instance if rate limiting enabled, None otherwise
        """
        if not self.settings.rate_limit_enabled:
            return None

        if self._websocket_rate_limiter is None:
            self._websocket_rate_limiter = RateLimiter(
                limit=self.settings.rate_limit_websocket_connections,
                window_seconds=self.settings.rate_limit_window_seconds,
            )

        return self._websocket_rate_limiter

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

    def get_validate_event_use_case(self) -> ValidateEventUseCase:
        """
        Get ValidateEventUseCase singleton.

        Returns:
            Use case instance
        """
        if self._validate_event_use_case is None:
            self._validate_event_use_case = ValidateEventUseCase()
        return self._validate_event_use_case

    def get_validate_message_use_case(self) -> ValidateMessageUseCase:
        """
        Get ValidateMessageUseCase singleton.

        Returns:
            Use case instance
        """
        if self._validate_message_use_case is None:
            self._validate_message_use_case = ValidateMessageUseCase(
                max_message_size=self.settings.max_message_size,
                max_string_length=self.settings.max_string_length,
                max_array_size=self.settings.max_array_size,
            )
        return self._validate_message_use_case

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
