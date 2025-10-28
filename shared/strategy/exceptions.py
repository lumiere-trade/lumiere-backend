"""
Trading Strategy Exceptions.

Custom exceptions for strategy execution and validation.
"""


class StrategyError(Exception):
    """Base exception for strategy errors."""


class InsufficientDataError(StrategyError):
    """Raised when there is not enough data for indicator calculation."""

    def __init__(self, indicator: str, required: int, available: int):
        """Initialize insufficient data error."""
        self.indicator = indicator
        self.required = required
        self.available = available
        message = (
            f"Insufficient data for {indicator}: "
            f"required {required}, available {available}"
        )
        super().__init__(message)


class InvalidIndicatorError(StrategyError):
    """Raised when an indicator name is invalid or not found."""

    def __init__(self, indicator: str, available: list = None):
        """Initialize invalid indicator error."""
        self.indicator = indicator
        self.available = available or []
        message = f"Invalid indicator: {indicator}"
        if available:
            message += f". Available: {', '.join(available)}"
        super().__init__(message)


class PositionError(StrategyError):
    """Raised when there is an error with position management."""


class RiskLimitError(StrategyError):
    """Raised when a risk limit would be violated."""

    def __init__(self, limit_type: str, limit_value: float, actual: float):
        """Initialize risk limit error."""
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.actual = actual
        message = (
            f"Risk limit violated - {limit_type}: "
            f"limit={limit_value}, actual={actual}"
        )
        super().__init__(message)
