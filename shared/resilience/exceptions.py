"""
Circuit breaker exceptions.

Defines exceptions thrown by circuit breaker.
"""


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""

    def __init__(self, message: str, breaker_name: str):
        """
        Initialize circuit breaker error.

        Args:
            message: Error message
            breaker_name: Name of the circuit breaker
        """
        self.message = message
        self.breaker_name = breaker_name
        super().__init__(self.message)


class CircuitBreakerOpenError(CircuitBreakerError):
    """
    Exception raised when circuit breaker is open.

    Indicates that the protected service is currently unavailable
    and calls are being blocked.
    """

    def __init__(self, breaker_name: str, failure_count: int):
        """
        Initialize circuit breaker open error.

        Args:
            breaker_name: Name of the circuit breaker
            failure_count: Number of failures that triggered the breaker
        """
        self.failure_count = failure_count
        message = (
            f"Circuit breaker '{breaker_name}' is OPEN "
            f"({failure_count} failures). Calls are blocked."
        )
        super().__init__(message, breaker_name)
