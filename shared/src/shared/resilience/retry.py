"""
Retry pattern with exponential backoff and jitter.

Provides automatic retry logic for transient failures with configurable
backoff strategies to prevent thundering herd problems.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class BackoffStrategy(str, Enum):
    """Backoff strategy for retries."""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    """Maximum number of retry attempts (including initial attempt)"""

    initial_delay: float = 1.0
    """Initial delay between retries in seconds"""

    max_delay: float = 60.0
    """Maximum delay between retries in seconds"""

    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    """Backoff strategy: exponential, linear, or constant"""

    backoff_multiplier: float = 2.0
    """Multiplier for exponential/linear backoff"""

    jitter: bool = True
    """Add random jitter to prevent thundering herd"""

    jitter_factor: float = 0.1
    """Jitter factor (0.0-1.0). 0.1 means ±10% randomness"""

    retry_on: tuple = (Exception,)
    """Exception types to retry on"""

    retry_on_result: Optional[Callable[[Any], bool]] = None
    """Function to check if result should trigger retry"""


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class Retry:
    """
    Retry handler with configurable backoff strategies.

    Example:
        retry = Retry(RetryConfig(max_attempts=5))

        @retry.decorator
        def fetch_data():
            response = requests.get("https://api.example.com/data")
            response.raise_for_status()
            return response.json()

        # Or use directly
        result = retry.execute(fetch_data)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for current attempt.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (
                self.config.backoff_multiplier**attempt
            )
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.initial_delay + (
                self.config.backoff_multiplier * attempt
            )
        else:  # CONSTANT
            delay = self.config.initial_delay

        # Cap at max_delay
        delay = min(delay, self.config.max_delay)

        # Add jitter if enabled
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0.0, delay + jitter)

        return delay

    def _should_retry_exception(self, exception: Exception) -> bool:
        """Check if exception should trigger retry."""
        return isinstance(exception, self.config.retry_on)

    def _should_retry_result(self, result: Any) -> bool:
        """Check if result should trigger retry."""
        if self.config.retry_on_result is None:
            return False
        return self.config.retry_on_result(result)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            RetryError: When all attempts exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)

                # Check if result should trigger retry
                if self._should_retry_result(result):
                    if attempt < self.config.max_attempts - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Retry condition met on result. "
                            f"Attempt {attempt + 1}/{self.config.max_attempts}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise RetryError(
                            f"All {self.config.max_attempts} attempts exhausted "
                            f"(result-based retry)",
                            attempts=self.config.max_attempts,
                        )

                # Success
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt "
                        f"{attempt + 1}/{self.config.max_attempts}"
                    )
                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry this exception
                if not self._should_retry_exception(e):
                    logger.error(f"Non-retryable exception: {type(e).__name__}: {e}")
                    raise

                # Last attempt - raise RetryError
                if attempt >= self.config.max_attempts - 1:
                    raise RetryError(
                        f"All {self.config.max_attempts} attempts exhausted. "
                        f"Last error: {type(e).__name__}: {e}",
                        attempts=self.config.max_attempts,
                        last_exception=e,
                    ) from e

                # Calculate delay and retry
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"{type(e).__name__}: {e}. "
                    f"Attempt {attempt + 1}/{self.config.max_attempts}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)

        # Should never reach here
        raise RetryError(
            f"Unexpected retry exhaustion",
            attempts=self.config.max_attempts,
            last_exception=last_exception,
        )

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            RetryError: When all attempts exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs)

                # Check if result should trigger retry
                if self._should_retry_result(result):
                    if attempt < self.config.max_attempts - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Retry condition met on result. "
                            f"Attempt {attempt + 1}/{self.config.max_attempts}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RetryError(
                            f"All {self.config.max_attempts} attempts exhausted "
                            f"(result-based retry)",
                            attempts=self.config.max_attempts,
                        )

                # Success
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt "
                        f"{attempt + 1}/{self.config.max_attempts}"
                    )
                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry this exception
                if not self._should_retry_exception(e):
                    logger.error(f"Non-retryable exception: {type(e).__name__}: {e}")
                    raise

                # Last attempt - raise RetryError
                if attempt >= self.config.max_attempts - 1:
                    raise RetryError(
                        f"All {self.config.max_attempts} attempts exhausted. "
                        f"Last error: {type(e).__name__}: {e}",
                        attempts=self.config.max_attempts,
                        last_exception=e,
                    ) from e

                # Calculate delay and retry
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"{type(e).__name__}: {e}. "
                    f"Attempt {attempt + 1}/{self.config.max_attempts}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        # Should never reach here
        raise RetryError(
            f"Unexpected retry exhaustion",
            attempts=self.config.max_attempts,
            last_exception=last_exception,
        )

    def decorator(self, func: Callable) -> Callable:
        """
        Decorator for retry logic.

        Example:
            retry = Retry(RetryConfig(max_attempts=3))

            @retry.decorator
            def my_function():
                return api_call()
        """
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.execute_async(func, *args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.execute(func, *args, **kwargs)

            return sync_wrapper


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator factory for retry logic.

    Example:
        @with_retry(RetryConfig(max_attempts=5, initial_delay=0.5))
        def fetch_data():
            return requests.get("https://api.example.com").json()
    """
    retry = Retry(config or RetryConfig())
    return retry.decorator


__all__ = [
    "Retry",
    "RetryConfig",
    "RetryError",
    "BackoffStrategy",
    "with_retry",
]
