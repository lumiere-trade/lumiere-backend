"""
MACD (Moving Average Convergence Divergence) indicator implementation.

Calculates trend-following momentum indicator.
Pure calculation with MACD line, signal line, and histogram.
"""

from typing import Dict

import pandas as pd

from shared.indicators.base import BaseIndicator


class MACDIndicator(BaseIndicator):
    """
    MACD indicator with line, signal, and histogram.

    Calculates:
    - MACD line = EMA(fast) - EMA(slow)
    - Signal line = EMA(MACD, signal_period)
    - Histogram = MACD - Signal

    Parameters:
        fast_period (int): Fast EMA period (default: 12)
        slow_period (int): Slow EMA period (default: 26)
        signal_period (int): Signal line EMA period (default: 9)

    Example:
        >>> macd = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
        >>> result = macd.calculate(df)
        >>> print(result['macd'].iloc[-1])
        >>> print(result['signal'].iloc[-1])
        >>> print(result['histogram'].iloc[-1])
    """

    def __init__(
        self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
    ):
        """
        Initialize MACD indicator.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
        """
        super().__init__(
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
        )
        self.fast_period = self.params["fast_period"]
        self.slow_period = self.params["slow_period"]
        self.signal_period = self.params["signal_period"]

    def validate_params(self) -> None:
        """
        Validate MACD parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        fast = self.params.get("fast_period", 12)
        slow = self.params.get("slow_period", 26)
        signal = self.params.get("signal_period", 9)

        if not isinstance(fast, int):
            raise ValueError(
                f"MACD fast_period must be integer, " f"got: {type(fast).__name__}"
            )

        if not isinstance(slow, int):
            raise ValueError(
                f"MACD slow_period must be integer, " f"got: {type(slow).__name__}"
            )

        if not isinstance(signal, int):
            raise ValueError(
                f"MACD signal_period must be integer, " f"got: {type(signal).__name__}"
            )

        if fast < 1:
            raise ValueError(f"MACD fast_period must be >= 1, got: {fast}")

        if slow < 1:
            raise ValueError(f"MACD slow_period must be >= 1, got: {slow}")

        if signal < 1:
            raise ValueError(f"MACD signal_period must be >= 1, got: {signal}")

        if fast >= slow:
            raise ValueError(
                f"MACD fast_period ({fast}) must be < " f"slow_period ({slow})"
            )

    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate MACD, signal line, and histogram.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Dict[str, pd.Series]: Dictionary with MACD values

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data
        """
        if "close" not in df.columns:
            raise KeyError("DataFrame must have 'close' column for MACD calculation")

        min_required = self.slow_period + self.signal_period
        if len(df) < min_required:
            raise ValueError(
                f"Insufficient data: need {min_required} candles, " f"got {len(df)}"
            )

        close = df["close"]

        ema_fast = close.ewm(
            span=self.fast_period, min_periods=self.fast_period, adjust=False
        ).mean()

        ema_slow = close.ewm(
            span=self.slow_period, min_periods=self.slow_period, adjust=False
        ).mean()

        macd_line = ema_fast - ema_slow

        signal_line = macd_line.ewm(
            span=self.signal_period, min_periods=self.signal_period, adjust=False
        ).mean()

        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }
