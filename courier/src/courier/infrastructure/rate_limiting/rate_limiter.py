"""
Rate limiter using token bucket algorithm with production logging.

Provides in-memory rate limiting for publish requests and WebSocket connections.
Supports both global and per-message-type rate limits.
For production with multiple instances, consider using Redis.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared.reporter import SystemReporter


class RateLimiter:
    """
    Token bucket rate limiter with per-message-type support.

    Implements sliding window rate limiting using token bucket algorithm.
    Tracks request timestamps per identifier and enforces configurable limits.
    Supports different rate limits per message type with fallback to default.

    Attributes:
        limit: Default maximum number of requests allowed in time window
        window_seconds: Time window in seconds
        per_type_limits: Optional per-message-type limits
        requests: Dictionary mapping identifiers to request timestamps
        type_requests: Dictionary mapping (identifier, type) to timestamps
        reporter: Optional SystemReporter for logging
    """

    def __init__(
        self,
        limit: int = 100,
        window_seconds: int = 60,
        per_type_limits: Optional[Dict[str, int]] = None,
        reporter: Optional[SystemReporter] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            limit: Default maximum requests allowed in window
            window_seconds: Time window in seconds
            per_type_limits: Optional per-message-type limits
                Example: {"trade": 50, "candles": 100, "strategy": 10}
            reporter: Optional SystemReporter for logging
        """
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.per_type_limits = per_type_limits or {}
        self.reporter = reporter

        # Global rate limiting (backward compatible)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)

        # Per-type rate limiting
        self.type_requests: Dict[tuple, List[datetime]] = defaultdict(list)

        # Log initialization
        if self.reporter:
            self.reporter.info(
                "RateLimiter initialized",
                context="RateLimiter",
                default_limit=limit,
                window_seconds=window_seconds,
                per_type_limits=list(self.per_type_limits.keys()),
                verbose_level=2,
            )

    async def check_rate_limit(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> bool:
        """
        Check if identifier is within rate limit.

        If message_type is provided and has a specific limit configured,
        uses that limit. Otherwise falls back to global limit.

        Implements sliding window algorithm:
        1. Remove expired timestamps (outside window)
        2. Check if remaining count exceeds limit
        3. Add current timestamp if allowed

        Args:
            identifier: Unique identifier (service name, user ID, etc.)
            message_type: Optional message type for per-type rate limiting

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        # Use per-type rate limiting if available
        if message_type and message_type in self.per_type_limits:
            return await self._check_type_rate_limit(
                identifier, message_type, now, cutoff
            )

        # Fall back to global rate limiting
        # Remove expired timestamps
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff
        ]

        # Check limit
        if len(self.requests[identifier]) >= self.limit:
            # Log rate limit exceeded (only at warning level)
            if self.reporter:
                remaining = self.get_remaining(identifier)
                retry_after = self.get_retry_after_seconds(identifier)
                self.reporter.warning(
                    "Global rate limit exceeded",
                    context="RateLimiter",
                    identifier=identifier,
                    limit=self.limit,
                    current_count=len(self.requests[identifier]),
                    remaining=remaining,
                    retry_after_seconds=retry_after,
                    verbose_level=2,
                )
            return False

        # Add current request
        self.requests[identifier].append(now)
        
        # Log at debug level only (avoid spam)
        if self.reporter:
            remaining = self.get_remaining(identifier)
            self.reporter.debug(
                "Rate limit check passed (global)",
                context="RateLimiter",
                identifier=identifier,
                current_count=len(self.requests[identifier]),
                limit=self.limit,
                remaining=remaining,
                verbose_level=3,
            )
        
        return True

    async def _check_type_rate_limit(
        self,
        identifier: str,
        message_type: str,
        now: datetime,
        cutoff: datetime,
    ) -> bool:
        """
        Check per-type rate limit.

        Args:
            identifier: Unique identifier
            message_type: Message type
            now: Current timestamp
            cutoff: Cutoff timestamp for sliding window

        Returns:
            True if allowed, False if rate limit exceeded
        """
        key = (identifier, message_type)
        type_limit = self.per_type_limits[message_type]

        # Remove expired timestamps
        self.type_requests[key] = [ts for ts in self.type_requests[key] if ts > cutoff]

        # Check limit
        if len(self.type_requests[key]) >= type_limit:
            # Log rate limit exceeded
            if self.reporter:
                remaining = self.get_remaining(identifier, message_type)
                retry_after = self.get_retry_after_seconds(identifier, message_type)
                self.reporter.warning(
                    "Per-type rate limit exceeded",
                    context="RateLimiter",
                    identifier=identifier,
                    message_type=message_type,
                    limit=type_limit,
                    current_count=len(self.type_requests[key]),
                    remaining=remaining,
                    retry_after_seconds=retry_after,
                    verbose_level=2,
                )
            return False

        # Add current request
        self.type_requests[key].append(now)
        
        # Log at debug level only (avoid spam)
        if self.reporter:
            remaining = self.get_remaining(identifier, message_type)
            self.reporter.debug(
                "Rate limit check passed (per-type)",
                context="RateLimiter",
                identifier=identifier,
                message_type=message_type,
                current_count=len(self.type_requests[key]),
                limit=type_limit,
                remaining=remaining,
                verbose_level=3,
            )
        
        return True

    def get_remaining(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> int:
        """
        Get remaining requests in current window.

        Args:
            identifier: Unique identifier
            message_type: Optional message type

        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        # Per-type limit
        if message_type and message_type in self.per_type_limits:
            key = (identifier, message_type)
            valid_requests = [
                ts for ts in self.type_requests.get(key, []) if ts > cutoff
            ]
            type_limit = self.per_type_limits[message_type]
            return max(0, type_limit - len(valid_requests))

        # Global limit
        valid_requests = [ts for ts in self.requests.get(identifier, []) if ts > cutoff]
        return max(0, self.limit - len(valid_requests))

    def get_reset_time(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> Optional[datetime]:
        """
        Get time when rate limit resets for identifier.

        Reset time is when oldest request exits the sliding window.

        Args:
            identifier: Unique identifier
            message_type: Optional message type

        Returns:
            Reset timestamp, or None if no requests
        """
        # Per-type limit
        if message_type and message_type in self.per_type_limits:
            key = (identifier, message_type)
            if key not in self.type_requests or not self.type_requests[key]:
                return None
            oldest = min(self.type_requests[key])
            return oldest + self.window

        # Global limit
        if identifier not in self.requests or not self.requests[identifier]:
            return None

        oldest = min(self.requests[identifier])
        return oldest + self.window

    def get_retry_after_seconds(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            identifier: Unique identifier
            message_type: Optional message type

        Returns:
            Seconds until reset (0 if can retry immediately)
        """
        reset_time = self.get_reset_time(identifier, message_type)
        if reset_time is None:
            return 0

        now = datetime.utcnow()
        if reset_time <= now:
            return 0

        return int((reset_time - now).total_seconds()) + 1

    def get_stats(
        self,
        identifier: str,
        message_type: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Get rate limit statistics for identifier.

        Args:
            identifier: Unique identifier
            message_type: Optional message type

        Returns:
            Dictionary with stats
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        # Per-type stats
        if message_type and message_type in self.per_type_limits:
            key = (identifier, message_type)
            valid_requests = [
                ts for ts in self.type_requests.get(key, []) if ts > cutoff
            ]
            type_limit = self.per_type_limits[message_type]

            return {
                "identifier": identifier,
                "message_type": message_type,
                "limit": type_limit,
                "window_seconds": int(self.window.total_seconds()),
                "current_count": len(valid_requests),
                "remaining": max(0, type_limit - len(valid_requests)),
                "reset_at": self.get_reset_time(identifier, message_type),
                "retry_after_seconds": self.get_retry_after_seconds(
                    identifier, message_type
                ),
            }

        # Global stats
        valid_requests = [ts for ts in self.requests.get(identifier, []) if ts > cutoff]

        return {
            "identifier": identifier,
            "message_type": None,
            "limit": self.limit,
            "window_seconds": int(self.window.total_seconds()),
            "current_count": len(valid_requests),
            "remaining": max(0, self.limit - len(valid_requests)),
            "reset_at": self.get_reset_time(identifier),
            "retry_after_seconds": self.get_retry_after_seconds(identifier),
        }

    def clear(
        self,
        identifier: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> None:
        """
        Clear rate limit data.

        Args:
            identifier: Optional specific identifier to clear
            message_type: Optional message type to clear
                If None and identifier provided, clears all types for identifier
                If both None, clears all data
        """
        if identifier is None and message_type is None:
            # Clear everything
            cleared_global = len(self.requests)
            cleared_typed = len(self.type_requests)
            self.requests.clear()
            self.type_requests.clear()
            
            if self.reporter:
                self.reporter.info(
                    "Rate limiter cleared (all data)",
                    context="RateLimiter",
                    cleared_global_identifiers=cleared_global,
                    cleared_typed_entries=cleared_typed,
                    verbose_level=2,
                )
                
        elif identifier and message_type:
            # Clear specific identifier + type
            key = (identifier, message_type)
            if key in self.type_requests:
                del self.type_requests[key]
                
                if self.reporter:
                    self.reporter.debug(
                        "Rate limiter cleared (specific type)",
                        context="RateLimiter",
                        identifier=identifier,
                        message_type=message_type,
                        verbose_level=3,
                    )
                    
        elif identifier:
            # Clear all data for identifier
            cleared_global = identifier in self.requests
            if cleared_global:
                del self.requests[identifier]
                
            # Clear all type-specific data for identifier
            keys_to_delete = [
                k for k in self.type_requests.keys() if k[0] == identifier
            ]
            cleared_types = len(keys_to_delete)
            for key in keys_to_delete:
                del self.type_requests[key]
                
            if self.reporter:
                self.reporter.debug(
                    "Rate limiter cleared (identifier)",
                    context="RateLimiter",
                    identifier=identifier,
                    cleared_global=cleared_global,
                    cleared_types=cleared_types,
                    verbose_level=3,
                )

    def get_all_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Get statistics for all tracked identifiers.

        Returns:
            Dictionary mapping identifiers to their stats
        """
        stats = {}

        # Global stats
        for identifier in self.requests.keys():
            stats[identifier] = self.get_stats(identifier)

        # Per-type stats
        for identifier, message_type in self.type_requests.keys():
            key = f"{identifier}:{message_type}"
            stats[key] = self.get_stats(identifier, message_type)

        # Log stats retrieval at debug level
        if self.reporter and stats:
            self.reporter.debug(
                "Rate limiter stats retrieved",
                context="RateLimiter",
                total_identifiers=len(stats),
                verbose_level=3,
            )

        return stats

    def get_configured_types(self) -> List[str]:
        """
        Get list of message types with configured limits.

        Returns:
            List of message type names
        """
        return list(self.per_type_limits.keys())
