"""
ATR (Average True Range) indicator implementation.

Measures market volatility using Wilder's smoothing method.
Pure calculation with optional percentage metric.
"""

from typing import Dict

import pandas as pd

from shared.indicators.base import BaseIndicator


class ATRIndicator(BaseIndicator):
    """
    ATR indicator with optional percentage calculation.

    Calculates:
    - True Range (TR) = max of:
      * high - low
      * |high - previous_close|
      * |low - previous_close|
    - ATR = Wilder's smoothing of TR
    - ATR % = (ATR / close) * 100

    Parameters:
        period (int): ATR smoothing period (default: 14)
        compute_percent (bool): Calculate ATR as % of price (default: True)

    Example:
        >>> atr = ATRIndicator(period=14, compute_percent=True)
        >>> result = atr.calculate(df)
        >>> print(result['atr'].iloc[-1])
        >>> print(result['atr_percent'].iloc[-1])
    """

    def __init__(self, period: int = 14, compute_percent: bool = True):
        """
        Initialize ATR indicator.

        Args:
            period: ATR smoothing period
            compute_percent: Calculate ATR as percentage of price
        """
        super().__init__(period=period, compute_percent=compute_percent)
        self.period = self.params["period"]
        self.compute_percent = self.params["compute_percent"]

    def validate_params(self) -> None:
        """
        Validate ATR parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        period = self.params.get("period", 14)

        if not isinstance(period, int):
            raise ValueError(
                f"ATR period must be integer, got: {type(period).__name__}"
            )

        if period < 1:
            raise ValueError(f"ATR period must be >= 1, got: {period}")

    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate ATR and optional percentage.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns

        Returns:
            Dict[str, pd.Series]: Dictionary with ATR values

        Raises:
            KeyError: If required columns missing
            ValueError: If insufficient data
        """
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(
                    f"DataFrame must have '{col}' column for ATR calculation"
                )

        if len(df) < self.period + 1:
            raise ValueError(
                f"Insufficient data: need {self.period + 1} candles, " f"got {len(df)}"
            )

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        alpha = 1.0 / self.period
        atr = tr.ewm(alpha=alpha, min_periods=self.period, adjust=False).mean()

        results = {
            "atr": atr,
        }

        if self.compute_percent:
            atr_percent = (atr / close) * 100
            results["atr_percent"] = atr_percent

        return results
