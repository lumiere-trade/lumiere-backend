"""
RSI (Relative Strength Index) indicator implementation.

Pure Wilder's smoothing calculation with zero dependencies.
"""

import numpy as np
import pandas as pd

from shared.indicators.base import BaseIndicator


class RSIIndicator(BaseIndicator):
    """
    RSI indicator using Wilder's smoothing method.

    Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

    Uses exponential weighted moving average (EWM) with alpha=1/period
    to match Wilder's original smoothing method.

    Parameters:
        period (int): RSI calculation period (default: 14)

    Example:
        >>> rsi = RSIIndicator(period=14)
        >>> rsi_values = rsi.calculate(df)
        >>> print(rsi_values.iloc[-1])  # Latest RSI value
        67.34
    """

    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.

        Args:
            period: RSI period (number of candles)
        """
        super().__init__(period=period)
        self.period = self.params["period"]

    def validate_params(self) -> None:
        """
        Validate RSI parameters.

        Raises:
            ValueError: If period is not integer >= 2
        """
        period = self.params.get("period", 14)

        if not isinstance(period, int):
            raise ValueError(
                f"RSI period must be integer, got: {type(period).__name__}"
            )

        if period < 2:
            raise ValueError(f"RSI period must be >= 2, got: {period}")

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI using Wilder's smoothing.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Series with RSI values (0-100), indexed by timestamp

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data (< period candles)
        """
        # Validate DataFrame
        if "close" not in df.columns:
            raise KeyError("DataFrame must have 'close' column for RSI calculation")

        if len(df) < self.period:
            raise ValueError(
                f"Insufficient data: need {self.period} candles, got {len(df)}"
            )

        close = df["close"]

        # Calculate price changes
        delta = close.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate Wilder's smoothed averages using EWM
        # alpha = 1/period matches Wilder's smoothing formula
        avg_gain = gains.ewm(
            alpha=1 / self.period, min_periods=self.period, adjust=False
        ).mean()

        avg_loss = losses.ewm(
            alpha=1 / self.period, min_periods=self.period, adjust=False
        ).mean()

        # Calculate Relative Strength (RS) and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Handle edge cases (neutral value when no data)
        rsi = rsi.fillna(50.0)

        return rsi

    def calculate_with_state(self, df: pd.DataFrame) -> tuple:
        """
        Calculate RSI and return final Wilder's smoothing state.

        Useful for initializing streaming/stateful indicators that need
        to continue RSI calculation incrementally.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Tuple of (rsi_series, state_dict) where state_dict contains:
                - 'avg_gain': final average gain value
                - 'avg_loss': final average loss value
                - 'prev_close': last close price

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data
        """
        # Calculate RSI series
        rsi_series = self.calculate(df)

        # Extract state using iterative Wilder's smoothing
        closes = df["close"].values
        deltas = np.diff(closes)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Initial averages
        avg_gain = np.mean(gains[: self.period])
        avg_loss = np.mean(losses[: self.period])

        # Apply Wilder's smoothing for remaining values
        for i in range(self.period, len(gains)):
            gain = gains[i]
            loss = losses[i]
            avg_gain = (avg_gain * (self.period - 1) + gain) / self.period
            avg_loss = (avg_loss * (self.period - 1) + loss) / self.period

        # Build state dict
        state = {
            "avg_gain": float(avg_gain),
            "avg_loss": float(avg_loss),
            "prev_close": float(closes[-1]),
        }

        return rsi_series, state
