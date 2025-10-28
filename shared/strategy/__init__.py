"""
Trading Strategy Domain Package.

This package contains the base classes and utilities for trading strategies.
Generated strategies from TSDL inherit from TradingStrategy base class.
"""

from shared.strategy.base_strategy import TradingStrategy
from shared.strategy.enums import (
    OrderType,
    PositionSide,
    PositionStatus,
)
from shared.strategy.exceptions import (
    InsufficientDataError,
    InvalidIndicatorError,
    PositionError,
    RiskLimitError,
    StrategyError,
)
from shared.strategy.position import Position

__all__ = [
    "TradingStrategy",
    "Position",
    "PositionSide",
    "OrderType",
    "PositionStatus",
    "StrategyError",
    "InsufficientDataError",
    "InvalidIndicatorError",
    "PositionError",
    "RiskLimitError",
]
