"""
Resilience patterns for distributed systems.

This module provides production-ready resilience patterns including:
- Circuit Breaker: Prevents cascading failures
- Timeout Protection: Prevents hanging operations
"""

from shared.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
)
from shared.resilience.exceptions import (
    CircuitBreakerError,
    CircuitBreakerOpenError,
)
from shared.resilience.timeout import (
    TimeoutContext,
    TimeoutError,
    timeout,
)

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    # Timeout
    "TimeoutContext",
    "TimeoutError",
    "timeout",
]
