"""
Trading Strategy Enums.

Defines enumerations for trading operations.
"""

from enum import Enum


class PositionSide(str, Enum):
    """Position side (direction)."""

    LONG = "long"
    SHORT = "short"

    def __str__(self) -> str:
        """String representation."""
        return self.value


class OrderType(str, Enum):
    """Order type for execution."""

    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

    def __str__(self) -> str:
        """String representation."""
        return self.value


class PositionStatus(str, Enum):
    """Position lifecycle status."""

    PENDING = "pending"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"

    def __str__(self) -> str:
        """String representation."""
        return self.value
