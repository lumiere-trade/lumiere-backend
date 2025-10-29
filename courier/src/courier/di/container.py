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
            "rate_limit_hits_per_type": {},
            "validation_failures": 0,
            "connection_rejections": 0,
            "connection_rejections_by_type": {},
            "start_time": datetime.utcnow(),
        }

    @property
    def connection_manager(self) -> ConnectionManager:
        """
        Get ConnectionManager singleton with configured connection limits.

        Returns:
            ConnectionManager instance
        """
        if self._connection_manager is None:
            self._connection_manager = ConnectionManager(
                max_total_connections=self.settings.max_total_connections,
                max_connections_per_user=self.settings.max_connections_per_user,
                max_clients_per_channel=self.settings.max_clients_per_channel,
            )
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
        Get WebSocket rate limiter singleton with per-message-type support.

        Returns:
            RateLimiter instance if rate limiting enabled, None otherwise
        """
        if not self.settings.rate_limit_enabled:
            return None

        if self._websocket_rate_limiter is None:
            self._websocket_rate_limiter = RateLimiter(
                limit=self.settings.rate_limit_websocket_connections,
                window_seconds=self.settings.rate_limit_window_seconds,
                per_type_limits=self.settings.rate_limit_per_message_type,
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
        Get ValidateEventUseCase singleton with configured size limits.

        Returns:
            Use case instance
        """
        if self._validate_event_use_case is None:
            self._validate_event_use_case = ValidateEventUseCase(
                max_event_size=self.settings.max_event_size,
                max_payload_size=self.settings.max_event_payload_size,
                max_metadata_size=self.settings.max_event_metadata_size,
            )
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

    def increment_rate_limit_hit(self, message_type: Optional[str] = None) -> None:
        """
        Increment rate limit hit counter.

        Args:
            message_type: Optional message type for per-type tracking
        """
        self.stats["rate_limit_hits"] += 1

        if message_type:
            if "rate_limit_hits_per_type" not in self.stats:
                self.stats["rate_limit_hits_per_type"] = {}
            if message_type not in self.stats["rate_limit_hits_per_type"]:
                self.stats["rate_limit_hits_per_type"][message_type] = 0
            self.stats["rate_limit_hits_per_type"][message_type] += 1

    def increment_connection_rejection(self, limit_type: str) -> None:
        """
        Increment connection rejection counter.

        Args:
            limit_type: Type of limit that caused rejection (global, per_user, per_channel)
        """
        self.stats["connection_rejections"] += 1

        if "connection_rejections_by_type" not in self.stats:
            self.stats["connection_rejections_by_type"] = {}
        if limit_type not in self.stats["connection_rejections_by_type"]:
            self.stats["connection_rejections_by_type"][limit_type] = 0
        self.stats["connection_rejections_by_type"][limit_type] += 1

    def get_uptime_seconds(self) -> float:
        """
        Get server uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return (datetime.utcnow() - self.stats["start_time"]).total_seconds()
