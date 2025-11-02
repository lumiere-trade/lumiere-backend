"""
Shared indicators package.

Pure calculation implementations with zero external dependencies.
Includes distributed registry for cross-process indicator access.
"""

from shared.indicators.base import BaseIndicator
from shared.indicators.distributed_registry import DistributedIndicatorRegistry
from shared.indicators.ema import EMAIndicator
from shared.indicators.patterns import PatternIndicator
from shared.indicators.rsi import RSIIndicator
from shared.indicators.sma import SMAIndicator

__all__ = [
    "BaseIndicator",
    "RSIIndicator",
    "SMAIndicator",
    "EMAIndicator",
    "PatternIndicator",
    "DistributedIndicatorRegistry",
]
