"""
Rate limiting using token bucket algorithm.

Provides rate limiting to prevent API abuse and protect external services
from being overwhelmed by too many requests.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter."""

    tokens_per_second: float = 10.0
    """Rate at which tokens are added to the bucket (requests per second)"""

    burst_size: int = 20
    """Maximum number of tokens in the bucket (burst capacity)"""

    initial_tokens: Optional[int] = None
    """Initial number of tokens (defaults to burst_size)"""


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float,
        tokens_available: float,
        tokens_required: float = 1.0,
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.tokens_available = tokens_available
        self.tokens_required = tokens_required


class TokenBucket:
    """
    Token bucket rate limiter.

    Uses token bucket algorithm for smooth rate limiting with burst capacity.

    Algorithm:
    - Bucket has a maximum capacity (burst_size)
    - Tokens are added at a constant rate (tokens_per_second)
    - Each request consumes tokens
    - If not enough tokens, request is rejected or waits

    Example:
        limiter = TokenBucket(
            RateLimitConfig(
                tokens_per_second=10.0,  # 10 requests/second
                burst_size=20             # Allow bursts up to 20
            )
        )

        # Acquire token (blocking)
        limiter.acquire()
        make_api_call()

        # Try acquire (non-blocking)
        if limiter.try_acquire():
            make_api_call()
        else:
            print("Rate limited!")

        # Async acquire
        await limiter.acquire_async()
        await make_async_api_call()
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._tokens = float(
            self.config.initial_tokens
            if self.config.initial_tokens is not None
            else self.config.burst_size
        )
        self._last_update = time.monotonic()
        self._lock = Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.config.tokens_per_second
        self._tokens = min(self._tokens + new_tokens, float(self.config.burst_size))
        self._last_update = now

    def _time_until_tokens(self, tokens: float = 1.0) -> float:
        """
        Calculate time until enough tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Time in seconds until tokens available (0 if available now)
        """
        tokens_needed = tokens - self._tokens
        if tokens_needed <= 0:
            return 0.0

        return tokens_needed / self.config.tokens_per_second

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        with self._lock:
            self._refill_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                logger.debug(
                    f"Acquired {tokens} token(s). " f"Remaining: {self._tokens:.2f}"
                )
                return True

            logger.debug(
                f"Rate limit exceeded. "
                f"Requested: {tokens}, Available: {self._tokens:.2f}"
            )
            return False

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None):
        """
        Acquire tokens, blocking until available.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)

        Raises:
            RateLimitExceeded: If timeout exceeded
        """
        start_time = time.monotonic()

        while True:
            with self._lock:
                self._refill_tokens()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    logger.debug(
                        f"Acquired {tokens} token(s). " f"Remaining: {self._tokens:.2f}"
                    )
                    return

                wait_time = self._time_until_tokens(tokens)

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed + wait_time > timeout:
                    raise RateLimitExceeded(
                        f"Rate limit timeout after {elapsed:.2f}s",
                        retry_after=wait_time,
                        tokens_available=self._tokens,
                        tokens_required=tokens,
                    )

            # Sleep and retry
            sleep_time = min(wait_time, 0.1)  # Check frequently
            logger.debug(
                f"Waiting {sleep_time:.2f}s for tokens. "
                f"Need: {tokens}, Have: {self._tokens:.2f}"
            )
            time.sleep(sleep_time)

    async def acquire_async(self, tokens: float = 1.0, timeout: Optional[float] = None):
        """
        Acquire tokens asynchronously, waiting until available.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)

        Raises:
            RateLimitExceeded: If timeout exceeded
        """
        start_time = time.monotonic()

        while True:
            with self._lock:
                self._refill_tokens()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    logger.debug(
                        f"Acquired {tokens} token(s). " f"Remaining: {self._tokens:.2f}"
                    )
                    return

                wait_time = self._time_until_tokens(tokens)

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed + wait_time > timeout:
                    raise RateLimitExceeded(
                        f"Rate limit timeout after {elapsed:.2f}s",
                        retry_after=wait_time,
                        tokens_available=self._tokens,
                        tokens_required=tokens,
                    )

            # Sleep and retry
            sleep_time = min(wait_time, 0.1)
            logger.debug(
                f"Async waiting {sleep_time:.2f}s for tokens. "
                f"Need: {tokens}, Have: {self._tokens:.2f}"
            )
            await asyncio.sleep(sleep_time)

    @property
    def available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self._lock:
            self._refill_tokens()
            return self._tokens

    @property
    def tokens_per_second(self) -> float:
        """Get configured rate (tokens per second)."""
        return self.config.tokens_per_second

    @property
    def burst_size(self) -> int:
        """Get configured burst size."""
        return self.config.burst_size

    def reset(self) -> None:
        """Reset the rate limiter to initial state."""
        with self._lock:
            self._tokens = float(
                self.config.initial_tokens
                if self.config.initial_tokens is not None
                else self.config.burst_size
            )
            self._last_update = time.monotonic()
            logger.info("Rate limiter reset")


class RateLimiterRegistry:
    """
    Registry for managing multiple rate limiters.

    Useful for per-user, per-endpoint, or per-service rate limiting.

    Example:
        registry = RateLimiterRegistry(
            default_config=RateLimitConfig(tokens_per_second=5)
        )

        # Get or create limiter for user
        limiter = registry.get_limiter("user_123")
        limiter.acquire()

        # Custom config for specific key
        registry.set_limiter(
            "premium_user_456",
            RateLimitConfig(tokens_per_second=50)
        )
    """

    def __init__(
        self,
        default_config: Optional[RateLimitConfig] = None,
    ):
        self.default_config = default_config or RateLimitConfig()
        self._limiters: Dict[str, TokenBucket] = {}
        self._lock = Lock()

    def get_limiter(self, key: str) -> TokenBucket:
        """
        Get or create rate limiter for key.

        Args:
            key: Identifier for the limiter (e.g., user_id, endpoint)

        Returns:
            TokenBucket instance for the key
        """
        with self._lock:
            if key not in self._limiters:
                self._limiters[key] = TokenBucket(self.default_config)
                logger.debug(f"Created rate limiter for key: {key}")

            return self._limiters[key]

    def set_limiter(self, key: str, config: RateLimitConfig) -> TokenBucket:
        """
        Set rate limiter with custom config for key.

        Args:
            key: Identifier for the limiter
            config: Custom rate limit configuration

        Returns:
            TokenBucket instance for the key
        """
        with self._lock:
            limiter = TokenBucket(config)
            self._limiters[key] = limiter
            logger.info(
                f"Set custom rate limiter for {key}: "
                f"{config.tokens_per_second} req/s"
            )
            return limiter

    def remove_limiter(self, key: str) -> None:
        """Remove rate limiter for key."""
        with self._lock:
            if key in self._limiters:
                del self._limiters[key]
                logger.debug(f"Removed rate limiter for key: {key}")

    def reset_all(self) -> None:
        """Reset all rate limiters."""
        with self._lock:
            for limiter in self._limiters.values():
                limiter.reset()
            logger.info("Reset all rate limiters")

    def clear(self) -> None:
        """Remove all rate limiters."""
        with self._lock:
            self._limiters.clear()
            logger.info("Cleared all rate limiters")


__all__ = [
    "TokenBucket",
    "RateLimitConfig",
    "RateLimitExceeded",
    "RateLimiterRegistry",
]
