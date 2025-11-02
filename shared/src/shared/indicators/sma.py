"""
SMA (Simple Moving Average) indicator implementation.

Pure calculation with optional additional metrics (distance, slope, position, crossover).
"""

from typing import Dict, Union

import pandas as pd

from shared.indicators.base import BaseIndicator


class SMAIndicator(BaseIndicator):
    """
    SMA indicator with optional additional metrics.

    Can compute:
    - SMA value (simple moving average)
    - Distance from price (percentage)
    - SMA slope (rate of change)
    - Price position relative to SMA (+1 above, -1 below, 0 equal)
    - Crossover detection (placeholder for compatibility)

    Parameters:
        period (int): SMA period (default: 20)
        compute_distance (bool): Calculate distance from price (default: True)
        compute_slope (bool): Calculate SMA slope (default: False)
        compute_position (bool): Calculate price position (default: False)
        compute_crossover (bool): Placeholder for compatibility (default: False)

    Example:
        >>> # Simple SMA only
        >>> sma = SMAIndicator(period=20)
        >>> result = sma.calculate(df)
        >>> print(result.iloc[-1])  # Latest SMA value

        >>> # SMA with distance
        >>> sma = SMAIndicator(period=20, compute_distance=True)
        >>> result = sma.calculate(df)
        >>> print(result['sma'].iloc[-1])
        >>> print(result['distance_pct'].iloc[-1])
    """

    def __init__(
        self,
        period: int = 20,
        compute_distance: bool = True,
        compute_slope: bool = False,
        compute_position: bool = False,
        compute_crossover: bool = False,
    ):
        """
        Initialize SMA indicator.

        Args:
            period: SMA period (number of candles)
            compute_distance: Calculate distance from price
            compute_slope: Calculate SMA slope
            compute_position: Calculate price position
            compute_crossover: Placeholder for compatibility (not implemented)
        """
        super().__init__(
            period=period,
            compute_distance=compute_distance,
            compute_slope=compute_slope,
            compute_position=compute_position,
            compute_crossover=compute_crossover,
        )
        self.period = self.params["period"]
        self.compute_distance = self.params["compute_distance"]
        self.compute_slope = self.params["compute_slope"]
        self.compute_position = self.params["compute_position"]
        self.compute_crossover = self.params["compute_crossover"]

    def validate_params(self) -> None:
        """
        Validate SMA parameters.

        Raises:
            ValueError: If period is not integer >= 2
        """
        period = self.params.get("period", 20)

        if not isinstance(period, int):
            raise ValueError(
                f"SMA period must be integer, got: {type(period).__name__}"
            )

        if period < 2:
            raise ValueError(f"SMA period must be >= 2, got: {period}")

    def calculate(self, df: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate SMA and optional metrics.

        Args:
            df: DataFrame with 'close' column

        Returns:
            pd.Series: If only SMA requested
            Dict[str, pd.Series]: If additional metrics requested

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data
        """
        # Validate DataFrame
        if "close" not in df.columns:
            raise KeyError("DataFrame must have 'close' column for SMA calculation")

        if len(df) < self.period:
            raise ValueError(
                f"Insufficient data: need {self.period} candles, got {len(df)}"
            )

        close = df["close"]

        # Calculate SMA
        sma = close.rolling(window=self.period, min_periods=self.period).mean()

        # If only SMA requested, return simple Series
        if not any([self.compute_distance, self.compute_slope, self.compute_position]):
            return sma

        # Otherwise, compute additional metrics
        results = {"sma": sma}

        if self.compute_distance:
            # Distance as percentage: (price - sma) / sma * 100
            distance = ((close - sma) / sma) * 100
            results["distance_pct"] = distance

        if self.compute_slope:
            # SMA slope: change over last 5 candles
            slope = sma.diff(5)
            results["slope"] = slope

        if self.compute_position:
            # Position: +1 if above, -1 if below, 0 if equal
            position = (close > sma).astype(int) - (close < sma).astype(int)
            results["position"] = position

        return results
