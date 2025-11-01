"""
Unit tests for CircuitBreaker.

Tests circuit breaker state machine and functionality.

Usage:
    python -m tests.unit.infrastructure.resilience.test_circuit_breaker
"""

import time

from shared.tests import LaborantTest

from shared.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)


class TestCircuitBreaker(LaborantTest):
    """Test CircuitBreaker core functionality."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures - creates fresh breaker for each test."""

    def _create_breaker(self, name="test_service"):
        """Create a fresh circuit breaker for each test."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,
            half_open_max_calls=2,
        )
        return CircuitBreaker(name, config)

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes in CLOSED state."""
        breaker = self._create_breaker()

        assert breaker.name == "test_service"
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_successful_call_in_closed_state(self):
        """Test successful call in CLOSED state."""
        breaker = self._create_breaker()

        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_failed_call_increments_failure_count(self):
        """Test failed call increments failure count."""
        breaker = self._create_breaker()

        def fail_func():
            raise ValueError("Test error")

        try:
            breaker.call(fail_func)
        except ValueError:
            pass

        assert breaker.failure_count == 1
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        breaker = self._create_breaker()

        def fail_func():
            raise ValueError("Test error")

        # Fail threshold times (3)
        for i in range(3):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass

        # Should now be OPEN
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 3

    def test_circuit_open_rejects_calls(self):
        """Test OPEN circuit rejects calls immediately."""
        breaker = self._create_breaker()

        # Trip the breaker
        breaker.trip()

        assert breaker.state == CircuitBreakerState.OPEN

        # Try to call - should raise CircuitBreakerOpenError
        def test_func():
            return "should not execute"

        try:
            breaker.call(test_func)
            assert False, "Expected CircuitBreakerOpenError"
        except CircuitBreakerOpenError as e:
            assert e.breaker_name == "test_service"
            assert "OPEN" in str(e)

    def test_circuit_transitions_to_half_open_after_timeout(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = self._create_breaker()

        # Trip the breaker
        breaker.trip()
        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_closes_on_success(self):
        """Test HALF_OPEN transitions to CLOSED on success threshold."""
        breaker = self._create_breaker()

        # Get to HALF_OPEN state
        breaker.trip()
        time.sleep(1.1)

        def success_func():
            return "success"

        # Need success_threshold (2) successes to close
        breaker.call(success_func)
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        breaker.call(success_func)
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Test HALF_OPEN transitions back to OPEN on failure."""
        breaker = self._create_breaker()

        # Get to HALF_OPEN state
        breaker.trip()
        time.sleep(1.1)

        # First success to enter HALF_OPEN
        breaker.call(lambda: "success")
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        # One failure should reopen
        def fail_func():
            raise ValueError("Test error")

        try:
            breaker.call(fail_func)
        except ValueError:
            pass

        assert breaker.state == CircuitBreakerState.OPEN

    def test_manual_reset(self):
        """Test manual reset to CLOSED state."""
        breaker = self._create_breaker()

        breaker.trip()
        assert breaker.state == CircuitBreakerState.OPEN

        breaker.reset()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_manual_trip(self):
        """Test manual trip to OPEN state."""
        breaker = self._create_breaker()

        assert breaker.state == CircuitBreakerState.CLOSED

        breaker.trip()
        assert breaker.state == CircuitBreakerState.OPEN

    def test_get_stats(self):
        """Test circuit breaker statistics."""
        breaker = self._create_breaker()

        def success_func():
            return "success"

        def fail_func():
            raise ValueError("Test error")

        # Some successes and failures
        breaker.call(success_func)
        try:
            breaker.call(fail_func)
        except ValueError:
            pass
        breaker.call(success_func)

        stats = breaker.get_stats()

        assert stats["name"] == "test_service"
        assert stats["state"] == "closed"
        assert stats["total_calls"] == 3
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 1
        assert "config" in stats


class TestCircuitBreakerStates(LaborantTest):
    """Test circuit breaker state transitions."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def _create_breaker(self):
        """Create fresh breaker for each test."""
        config = CircuitBreakerConfig(
            failure_threshold=2, success_threshold=1, timeout=0.5
        )
        return CircuitBreaker("test", config)

    def test_closed_to_open_transition(self):
        """Test CLOSED -> OPEN transition."""
        breaker = self._create_breaker()

        def fail_func():
            raise ValueError()

        assert breaker.state == CircuitBreakerState.CLOSED

        # Fail twice to open
        for _ in range(2):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN

    def test_open_to_half_open_transition(self):
        """Test OPEN -> HALF_OPEN transition."""
        breaker = self._create_breaker()

        breaker.trip()
        assert breaker.state == CircuitBreakerState.OPEN

        time.sleep(0.6)  # Wait for timeout

        # First call after timeout transitions to HALF_OPEN
        breaker.call(lambda: "ok")
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_to_closed_transition(self):
        """Test HALF_OPEN -> CLOSED transition."""
        breaker = self._create_breaker()

        breaker.trip()
        time.sleep(0.6)

        # Enter HALF_OPEN and succeed
        breaker.call(lambda: "ok")
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_half_open_to_open_transition(self):
        """Test HALF_OPEN -> OPEN transition."""
        breaker = self._create_breaker()

        breaker.trip()
        time.sleep(0.6)

        # Enter HALF_OPEN with success
        breaker.call(lambda: "ok")

        # Fail - should go back to OPEN
        try:
            breaker.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert breaker.state == CircuitBreakerState.OPEN


class TestCircuitBreakerConfig(LaborantTest):
    """Test circuit breaker configuration."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=120.0,
            half_open_max_calls=5,
        )

        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 120.0
        assert config.half_open_max_calls == 5


class TestCircuitBreakerThreadSafety(LaborantTest):
    """Test circuit breaker thread safety."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_concurrent_calls_safe(self):
        """Test that concurrent calls are thread-safe."""
        import threading

        breaker = CircuitBreaker("thread_test")
        results = []
        errors = []

        def worker():
            try:
                result = breaker.call(lambda: "ok")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should succeed
        assert len(results) == 10
        assert len(errors) == 0


if __name__ == "__main__":
    TestCircuitBreaker.run_as_main()
