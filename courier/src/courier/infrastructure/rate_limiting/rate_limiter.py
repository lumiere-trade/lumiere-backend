"""
Rate limiter using token bucket algorithm.

Provides in-memory rate limiting for publish requests and WebSocket connections.
For production with multiple instances, consider using Redis.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class RateLimiter:
    """
    Token bucket rate limiter.

    Implements sliding window rate limiting using token bucket algorithm.
    Tracks request timestamps per identifier and enforces configurable limits.

    Attributes:
        limit: Maximum number of requests allowed in time window
        window_seconds: Time window in seconds
        requests: Dictionary mapping identifiers to request timestamps
    """

    def __init__(
        self,
        limit: int = 100,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.

        Args:
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)

    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier is within rate limit.

        Implements sliding window algorithm:
        1. Remove expired timestamps (outside window)
        2. Check if remaining count exceeds limit
        3. Add current timestamp if allowed

        Args:
            identifier: Unique identifier (service name, user ID, etc.)

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        # Remove expired timestamps
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff
        ]

        # Check limit
        if len(self.requests[identifier]) >= self.limit:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests in current window.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        # Count valid requests
        valid_requests = [
            ts for ts in self.requests.get(identifier, []) if ts > cutoff
        ]

        return max(0, self.limit - len(valid_requests))

    def get_reset_time(self, identifier: str) -> Optional[datetime]:
        """
        Get time when rate limit resets for identifier.

        Reset time is when oldest request exits the sliding window.

        Args:
            identifier: Unique identifier

        Returns:
            Reset timestamp, or None if no requests
        """
        if identifier not in self.requests or not self.requests[identifier]:
            return None

        oldest = min(self.requests[identifier])
        return oldest + self.window

    def get_retry_after_seconds(self, identifier: str) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            identifier: Unique identifier

        Returns:
            Seconds until reset (0 if can retry immediately)
        """
        reset_time = self.get_reset_time(identifier)
        if reset_time is None:
            return 0

        now = datetime.utcnow()
        if reset_time <= now:
            return 0

        return int((reset_time - now).total_seconds()) + 1

    def get_stats(self, identifier: str) -> Dict[str, any]:
        """
        Get rate limit statistics for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with stats
        """
        now = datetime.utcnow()
        cutoff = now - self.window

        valid_requests = [
            ts for ts in self.requests.get(identifier, []) if ts > cutoff
        ]

        return {
            "identifier": identifier,
            "limit": self.limit,
            "window_seconds": int(self.window.total_seconds()),
            "current_count": len(valid_requests),
            "remaining": max(0, self.limit - len(valid_requests)),
            "reset_at": self.get_reset_time(identifier),
            "retry_after_seconds": self.get_retry_after_seconds(identifier),
        }

    def clear(self, identifier: Optional[str] = None) -> None:
        """
        Clear rate limit data.

        Args:
            identifier: Optional specific identifier to clear.
                       If None, clears all data.
        """
        if identifier is None:
            self.requests.clear()
        elif identifier in self.requests:
            del self.requests[identifier]

    def get_all_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Get statistics for all tracked identifiers.

        Returns:
            Dictionary mapping identifiers to their stats
        """
        return {
            identifier: self.get_stats(identifier)
            for identifier in self.requests.keys()
        }
