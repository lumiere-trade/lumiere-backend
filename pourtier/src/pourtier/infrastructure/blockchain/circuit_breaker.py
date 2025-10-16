"""
Circuit breaker pattern for blockchain service resilience.
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Optional


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Tracks failures and automatically stops calling failing services.
    After a timeout, allows a test request to check if service recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again (half-open)
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. "
                        f"Failures: {self._failure_count}/{self.failure_threshold}. "
                        f"Retry after {self.recovery_timeout}s."
                    )

        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except self.expected_exception as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time passed to try again.

        Returns:
            True if should attempt reset to HALF_OPEN
        """
        if self._last_failure_time is None:
            return False

        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._state = CircuitState.CLOSED

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dict with state, failure_count, last_failure_time
        """
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }
