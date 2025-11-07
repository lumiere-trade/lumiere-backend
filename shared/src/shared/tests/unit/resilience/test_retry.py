"""
Unit tests for Retry pattern.

Tests retry logic with various backoff strategies, jitter, and error handling.

Usage:
    python tests/unit/resilience/test_retry.py
    laborant test shared --unit
"""

import asyncio

from shared.resilience.retry import (
    BackoffStrategy,
    Retry,
    RetryConfig,
    RetryError,
    with_retry,
)
from shared.tests import LaborantTest


class TestRetryPattern(LaborantTest):
    """Unit tests for Retry pattern."""

    component_name = "shared"
    test_category = "unit"

    # ================================================================
    # Configuration tests
    # ================================================================

    def test_retry_config_defaults(self):
        """Test RetryConfig default values."""
        self.reporter.info("Testing RetryConfig defaults", context="Test")

        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.1
        assert config.retry_on == (Exception,)
        assert config.retry_on_result is None

        self.reporter.info("Default config values correct", context="Test")

    def test_retry_config_custom_values(self):
        """Test RetryConfig with custom values."""
        self.reporter.info("Testing custom RetryConfig", context="Test")

        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            backoff_strategy=BackoffStrategy.LINEAR,
            backoff_multiplier=1.5,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.backoff_strategy == BackoffStrategy.LINEAR
        assert config.backoff_multiplier == 1.5
        assert config.jitter is False

        self.reporter.info("Custom config values correct", context="Test")

    # ================================================================
    # Basic retry tests
    # ================================================================

    def test_successful_operation_no_retry(self):
        """Test successful operation requires no retry."""
        self.reporter.info("Testing successful operation without retry", context="Test")

        retry = Retry(RetryConfig(max_attempts=3))
        call_count = 0

        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry.execute(successful_func)

        assert result == "success"
        assert call_count == 1

        self.reporter.info("Operation succeeded on first try", context="Test")

    def test_retry_after_transient_failure(self):
        """Test retry after transient failure."""
        self.reporter.info("Testing retry after failure", context="Test")

        retry = Retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        call_count = 0

        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = retry.execute(failing_then_success)

        assert result == "success"
        assert call_count == 3

        self.reporter.info("Operation succeeded after 2 retries", context="Test")

    def test_exhausted_retries_raises_error(self):
        """Test RetryError raised when all attempts exhausted."""
        self.reporter.info("Testing retry exhaustion", context="Test")

        retry = Retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        call_count = 0

        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        try:
            retry.execute(always_fails)
            assert False, "Should have raised RetryError"
        except RetryError as e:
            assert e.attempts == 3
            assert isinstance(e.last_exception, ValueError)
            assert "Permanent error" in str(e.last_exception)
            self.reporter.info("RetryError raised correctly", context="Test")

        assert call_count == 3

    # ================================================================
    # Backoff strategy tests
    # ================================================================

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        self.reporter.info("Testing exponential backoff", context="Test")

        retry = Retry(
            RetryConfig(
                initial_delay=1.0,
                backoff_multiplier=2.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                jitter=False,
            )
        )

        assert retry._calculate_delay(0) == 1.0
        assert retry._calculate_delay(1) == 2.0
        assert retry._calculate_delay(2) == 4.0

        self.reporter.info("Exponential backoff correct", context="Test")

    def test_linear_backoff_calculation(self):
        """Test linear backoff delay calculation."""
        self.reporter.info("Testing linear backoff", context="Test")

        retry = Retry(
            RetryConfig(
                initial_delay=1.0,
                backoff_multiplier=0.5,
                backoff_strategy=BackoffStrategy.LINEAR,
                jitter=False,
            )
        )

        assert retry._calculate_delay(0) == 1.0
        assert retry._calculate_delay(1) == 1.5
        assert retry._calculate_delay(2) == 2.0

        self.reporter.info("Linear backoff correct", context="Test")

    def test_constant_backoff_calculation(self):
        """Test constant backoff delay calculation."""
        self.reporter.info("Testing constant backoff", context="Test")

        retry = Retry(
            RetryConfig(
                initial_delay=2.0,
                backoff_strategy=BackoffStrategy.CONSTANT,
                jitter=False,
            )
        )

        assert retry._calculate_delay(0) == 2.0
        assert retry._calculate_delay(1) == 2.0
        assert retry._calculate_delay(2) == 2.0

        self.reporter.info("Constant backoff correct", context="Test")

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        self.reporter.info("Testing max_delay cap", context="Test")

        retry = Retry(
            RetryConfig(
                initial_delay=1.0,
                max_delay=5.0,
                backoff_multiplier=2.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                jitter=False,
            )
        )

        delay = retry._calculate_delay(3)
        assert delay == 5.0

        self.reporter.info("max_delay cap working", context="Test")

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        self.reporter.info("Testing jitter randomness", context="Test")

        retry = Retry(
            RetryConfig(
                initial_delay=10.0,
                jitter=True,
                jitter_factor=0.1,
                backoff_strategy=BackoffStrategy.CONSTANT,
            )
        )

        delays = [retry._calculate_delay(0) for _ in range(10)]
        unique_delays = len(set(delays))
        assert unique_delays > 1

        for delay in delays:
            assert 9.0 <= delay <= 11.0

        self.reporter.info("Jitter working correctly", context="Test")

    # ================================================================
    # Exception handling tests
    # ================================================================

    def test_retry_specific_exceptions(self):
        """Test retry only on specific exception types."""
        self.reporter.info("Testing specific exception retry", context="Test")

        retry = Retry(
            RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                retry_on=(ValueError,),
            )
        )

        call_count = 0

        def fails_with_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retryable")
            return "success"

        result = retry.execute(fails_with_value_error)
        assert result == "success"
        assert call_count == 2

        self.reporter.info("Specific exceptions retried", context="Test")

    def test_non_retryable_exception_propagates(self):
        """Test non-retryable exceptions propagate immediately."""
        self.reporter.info(
            "Testing non-retryable exception propagation", context="Test"
        )

        retry = Retry(
            RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                retry_on=(ValueError,),
            )
        )

        call_count = 0

        def fails_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable")

        try:
            retry.execute(fails_with_type_error)
            assert False, "Should have raised TypeError"
        except TypeError as e:
            assert "Non-retryable" in str(e)
            self.reporter.info("Non-retryable exception propagated", context="Test")

        assert call_count == 1

    # ================================================================
    # Result-based retry tests
    # ================================================================

    def test_retry_on_result_condition(self):
        """Test retry based on result value."""
        self.reporter.info("Testing result-based retry", context="Test")

        call_count = 0

        def should_retry(result):
            return result is None

        retry = Retry(
            RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                retry_on_result=should_retry,
            )
        )

        def returns_none_then_value():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return None
            return "success"

        result = retry.execute(returns_none_then_value)
        assert result == "success"
        assert call_count == 2

        self.reporter.info("Result-based retry working", context="Test")

    def test_result_retry_exhaustion(self):
        """Test RetryError when result condition never met."""
        self.reporter.info("Testing result retry exhaustion", context="Test")

        def should_retry(result):
            return result == "retry"

        retry = Retry(
            RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                retry_on_result=should_retry,
            )
        )

        call_count = 0

        def always_returns_retry():
            nonlocal call_count
            call_count += 1
            return "retry"

        try:
            retry.execute(always_returns_retry)
            assert False, "Should have raised RetryError"
        except RetryError as e:
            assert e.attempts == 3
            self.reporter.info("Result retry exhausted correctly", context="Test")

        assert call_count == 3

    # ================================================================
    # Decorator tests
    # ================================================================

    def test_decorator_basic(self):
        """Test basic decorator usage."""
        self.reporter.info("Testing retry decorator", context="Test")

        retry = Retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        call_count = 0

        @retry.decorator
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry me")
            return "success"

        result = decorated_func()
        assert result == "success"
        assert call_count == 2

        self.reporter.info("Decorator working correctly", context="Test")

    def test_with_retry_decorator_factory(self):
        """Test with_retry decorator factory."""
        self.reporter.info("Testing with_retry factory", context="Test")

        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry me")
            return "success"

        result = decorated_func()
        assert result == "success"
        assert call_count == 2

        self.reporter.info("with_retry factory working", context="Test")

    # ================================================================
    # Async tests
    # ================================================================

    def test_async_retry_success(self):
        """Test async retry with successful result."""
        self.reporter.info("Testing async retry success", context="Test")

        retry = Retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        call_count = 0

        async def async_failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Async transient error")
            return "async success"

        result = asyncio.run(retry.execute_async(async_failing_then_success))
        assert result == "async success"
        assert call_count == 2

        self.reporter.info("Async retry succeeded", context="Test")

    def test_async_decorator(self):
        """Test async decorator usage."""
        self.reporter.info("Testing async decorator", context="Test")

        retry = Retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        call_count = 0

        @retry.decorator
        async def async_decorated():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Async retry")
            return "async decorated success"

        result = asyncio.run(async_decorated())
        assert result == "async decorated success"
        assert call_count == 2

        self.reporter.info("Async decorator working", context="Test")


if __name__ == "__main__":
    TestRetryPattern.run_as_main()
