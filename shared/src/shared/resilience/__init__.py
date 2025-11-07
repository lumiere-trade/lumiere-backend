"""
Resilience patterns for distributed systems.

This module provides production-ready resilience patterns including:
- Circuit Breaker: Prevents cascading failures
- Timeout Protection: Prevents hanging operations
- Retry: Automatic retry with exponential backoff
- Rate Limiting: Token bucket rate limiter
- Idempotency: Exactly-once execution guarantee
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
from shared.resilience.idempotency import (
    DuplicateRequestError,
    IdempotencyError,
    IdempotencyKey,
    IdempotencyStore,
    InMemoryIdempotencyStore,
    idempotent,
)
from shared.resilience.rate_limiter import (
    RateLimitConfig,
    RateLimiterRegistry,
    RateLimitExceeded,
    TokenBucket,
)
from shared.resilience.retry import (
    BackoffStrategy,
    Retry,
    RetryConfig,
    RetryError,
    with_retry,
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
    # Retry
    "Retry",
    "RetryConfig",
    "RetryError",
    "BackoffStrategy",
    "with_retry",
    # Rate Limiting
    "TokenBucket",
    "RateLimitConfig",
    "RateLimitExceeded",
    "RateLimiterRegistry",
    # Idempotency
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "IdempotencyKey",
    "IdempotencyError",
    "DuplicateRequestError",
    "idempotent",
]
