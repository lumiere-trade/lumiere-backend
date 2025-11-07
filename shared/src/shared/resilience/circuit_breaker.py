"""
Circuit Breaker Pattern Implementation.

Prevents cascading failures by stopping calls to failing services.

State Machine:
    CLOSED -> OPEN -> HALF_OPEN -> CLOSED
           |                    |
           +--------------------+

- CLOSED: Normal operation, counting failures
- OPEN: Blocking all calls, waiting for timeout
- HALF_OPEN: Testing if service recovered
"""

import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any, Callable, Optional

from .exceptions import CircuitBreakerOpenError


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """
    Circuit breaker configuration.

    Attributes:
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes to close from half-open
        timeout: Seconds to wait before trying half-open
        half_open_max_calls: Max concurrent calls in half-open state
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    The circuit breaker monitors for failures and stops calling a failing
    service to give it time to recover.

    Example:
        breaker = CircuitBreaker("my_service")

        try:
            result = breaker.call(risky_function, arg1, arg2)
        except CircuitBreakerOpenError:
            # Handle circuit open
            return fallback_value
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            config: Configuration (uses defaults if not provided)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        # Thread safety
        self._lock = Lock()

        # Statistics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._state_changes = 0

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        return self._success_count

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result from function

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            self._total_calls += 1

            # Check if we should attempt the call
            if not self._can_attempt():
                raise CircuitBreakerOpenError(self.name, self._failure_count)

            # Mark as attempting (for half-open state)
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._half_open_calls += 1

        # Execute function (outside lock to avoid blocking)
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result from function

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            self._total_calls += 1

            # Check if we should attempt the call
            if not self._can_attempt():
                raise CircuitBreakerOpenError(self.name, self._failure_count)

            # Mark as attempting (for half-open state)
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._half_open_calls += 1

        # Execute async function (outside lock to avoid blocking)
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _can_attempt(self) -> bool:
        """
        Check if we can attempt a call.

        Returns:
            True if call should be attempted
        """
        if self._state == CircuitBreakerState.CLOSED:
            return True

        if self._state == CircuitBreakerState.OPEN:
            # Check if timeout has expired
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False

        if self._state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in half-open
            return self._half_open_calls < self.config.half_open_max_calls

        return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open."""
        if self._last_failure_time is None:
            return False
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._total_successes += 1

            if self._state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

            elif self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1

                # Check if we have enough successes to close
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitBreakerState.CLOSED:
                # Check if we should open
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

            elif self._state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitBreakerState.OPEN
        self._success_count = 0
        self._half_open_calls = 0
        self._state_changes += 1

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self._state = CircuitBreakerState.HALF_OPEN
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._state_changes += 1

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
        self._state_changes += 1

    def reset(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        Useful for administrative control or testing.
        """
        with self._lock:
            self._transition_to_closed()

    def trip(self) -> None:
        """
        Manually trip circuit breaker to OPEN state.

        Useful for administrative control or testing.
        """
        with self._lock:
            self._failure_count = self.config.failure_threshold
            self._last_failure_time = time.time()
            self._transition_to_open()

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "total_calls": self._total_calls,
                "total_failures": self._total_failures,
                "total_successes": self._total_successes,
                "state_changes": self._state_changes,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout,
                    "half_open_max_calls": self.config.half_open_max_calls,
                },
            }
