"""
Rate Limiter Adapter - wraps shared RateLimiter with Courier-specific interface.

Clean Architecture: Infrastructure layer adapts shared component to domain needs.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared.resilience.rate_limiter import (
    RateLimitConfig,
    RateLimiterRegistry,
)


class RateLimiter:
    """
    Rate Limiter Adapter for Courier.

    Wraps shared RateLimiterRegistry to provide Courier-specific interface
    with per-message-type rate limiting support.

    Architecture:
        - Uses shared TokenBucket for actual rate limiting
        - Provides async interface required by Courier
        - Maintains backward compatibility with existing code
        - Supports per-type limits via registry keys

    Attributes:
        default_limit: Default requests per window
        window_seconds: Time window in seconds
        per_type_limits: Per-message-type limits
        _registry: Shared RateLimiterRegistry instance
    """

    def __init__(
        self,
        limit: int = 100,
        window_seconds: int = 60,
        per_type_limits: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize adapter.

        Args:
            limit: Default maximum requests allowed in window
            window_seconds: Time window in seconds
            per_type_limits: Optional per-message-type limits
                Example: {"trade": 50, "candles": 100}
        """
        self.default_limit = limit
        self.window_seconds = window_seconds
        self.per_type_limits = per_type_limits or {}

        # Calculate tokens_per_second from limit and window
        tokens_per_second = limit / window_seconds

        # Create shared registry with default config
        default_config = RateLimitConfig(
            tokens_per_second=tokens_per_second,
            burst_size=limit,
        )
        self._registry = RateLimiterRegistry(default_config=default_config)

    def _get_limiter_key(
        self, identifier: str, message_type: Optional[str] = None
    ) -> str:
        """Generate registry key for limiter."""
        if message_type and message_type in self.per_type_limits:
            return f"{identifier}:{message_type}"
        return identifier

    def _get_limiter(self, identifier: str, message_type: Optional[str] = None):
        """Get or create rate limiter for identifier."""
        key = self._get_limiter_key(identifier, message_type)

        # Use per-type config if available
        if message_type and message_type in self.per_type_limits:
            type_tokens_per_second = (
                self.per_type_limits[message_type] / self.window_seconds
            )
            type_config = RateLimitConfig(
                tokens_per_second=type_tokens_per_second,
                burst_size=self.per_type_limits[message_type],
            )
            return self._registry.set_limiter(key, type_config)

        # Use default config
        return self._registry.get_limiter(key)

    async def check_rate_limit(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> bool:
        """
        Check if identifier is within rate limit.

        Args:
            identifier: Unique identifier
            message_type: Optional message type

        Returns:
            True if allowed, False if rate limited
        """
        limiter = self._get_limiter(identifier, message_type)
        return limiter.try_acquire(tokens=1.0)

    def get_remaining(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> int:
        """Get remaining requests (approximate)."""
        limiter = self._get_limiter(identifier, message_type)
        return int(limiter.available_tokens)

    def get_retry_after_seconds(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> int:
        """Get seconds until rate limit resets."""
        limiter = self._get_limiter(identifier, message_type)
        available = limiter.available_tokens

        if available >= 1.0:
            return 0

        # Calculate time to refill 1 token
        tokens_needed = 1.0 - available
        seconds = tokens_needed / limiter.tokens_per_second

        return int(seconds) + 1

    def get_stats(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> Dict[str, any]:
        """Get rate limit statistics."""
        limiter = self._get_limiter(identifier, message_type)

        limit = (
            self.per_type_limits.get(message_type, self.default_limit)
            if message_type
            else self.default_limit
        )

        return {
            "identifier": identifier,
            "message_type": message_type,
            "limit": limit,
            "window_seconds": self.window_seconds,
            "remaining": int(limiter.available_tokens),
            "retry_after_seconds": self.get_retry_after_seconds(
                identifier, message_type
            ),
            "reset_at": datetime.utcnow() + timedelta(seconds=self.window_seconds),
        }

    def clear(
        self,
        identifier: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> None:
        """Clear rate limit data."""
        if identifier is None:
            self._registry.clear()
        else:
            key = self._get_limiter_key(identifier, message_type)
            self._registry.remove_limiter(key)

    def get_configured_types(self) -> List[str]:
        """Get list of message types with configured limits."""
        return list(self.per_type_limits.keys())
