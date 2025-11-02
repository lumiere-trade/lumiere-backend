"""
EMA (Exponential Moving Average) indicator implementation.

Pure calculation with optional distance metric.
"""

from typing import Dict, Union

import pandas as pd

from shared.indicators.base import BaseIndicator


class EMAIndicator(BaseIndicator):
    """
    EMA indicator with optional distance calculation.

    Uses pandas exponential weighted moving average (EWM) with span parameter.

    Parameters:
        period (int): EMA period/span (default: 12)
        compute_distance (bool): Calculate distance from price (default: False)

    Example:
        >>> # Simple EMA
        >>> ema = EMAIndicator(period=12)
        >>> result = ema.calculate(df)
        >>> print(result.iloc[-1])

        >>> # EMA with distance
        >>> ema = EMAIndicator(period=12, compute_distance=True)
        >>> result = ema.calculate(df)
        >>> print(result['ema'].iloc[-1])
        >>> print(result['distance_pct'].iloc[-1])
    """

    def __init__(self, period: int = 12, compute_distance: bool = False):
        """
        Initialize EMA indicator.

        Args:
            period: EMA period/span (number of candles)
            compute_distance: Calculate distance from price as percentage
        """
        super().__init__(period=period, compute_distance=compute_distance)
        self.period = self.params["period"]
        self.compute_distance = self.params["compute_distance"]

    def validate_params(self) -> None:
        """
        Validate EMA parameters.

        Raises:
            ValueError: If period is not integer >= 2
        """
        period = self.params.get("period", 12)

        if not isinstance(period, int):
            raise ValueError(
                f"EMA period must be integer, got: {type(period).__name__}"
            )

        if period < 2:
            raise ValueError(f"EMA period must be >= 2, got: {period}")

    def calculate(self, df: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate EMA and optional distance.

        Args:
            df: DataFrame with 'close' column

        Returns:
            pd.Series: If only EMA requested
            Dict[str, pd.Series]: If distance requested

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data
        """
        if "close" not in df.columns:
            raise KeyError("DataFrame must have 'close' column for EMA calculation")

        if len(df) < self.period:
            raise ValueError(
                f"Insufficient data: need {self.period} candles, " f"got {len(df)}"
            )

        close = df["close"]

        ema = close.ewm(span=self.period, min_periods=self.period, adjust=False).mean()

        if not self.compute_distance:
            return ema

        distance = ((close - ema) / ema) * 100

        return {"ema": ema, "distance_pct": distance}
