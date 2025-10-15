"""
Stochastic Oscillator indicator implementation.

Calculates momentum indicator comparing closing price to price range.
Pure calculation with %K and %D lines.
"""

from typing import Dict

import pandas as pd

from shared.indicators.base import BaseIndicator


class StochasticIndicator(BaseIndicator):
    """
    Stochastic Oscillator with %K and %D lines.

    Calculates:
    - %K = (close - lowest_low) / (highest_high - lowest_low) * 100
    - %D = SMA(%K, smooth_period)

    Parameters:
        k_period (int): Period for %K calculation (default: 14)
        d_period (int): Period for %D smoothing (default: 3)
        smooth_k (int): Smoothing period for %K (default: 3)

    Example:
        >>> stoch = StochasticIndicator(k_period=14, d_period=3, smooth_k=3)
        >>> result = stoch.calculate(df)
        >>> print(result['stoch_k'].iloc[-1])
        >>> print(result['stoch_d'].iloc[-1])
    """

    def __init__(self, k_period: int = 14, d_period: int = 3, smooth_k: int = 3):
        """
        Initialize Stochastic indicator.

        Args:
            k_period: Period for %K calculation
            d_period: Period for %D smoothing
            smooth_k: Smoothing period for %K
        """
        super().__init__(k_period=k_period, d_period=d_period, smooth_k=smooth_k)
        self.k_period = self.params["k_period"]
        self.d_period = self.params["d_period"]
        self.smooth_k = self.params["smooth_k"]

    def validate_params(self) -> None:
        """
        Validate Stochastic parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        k_period = self.params.get("k_period", 14)
        d_period = self.params.get("d_period", 3)
        smooth_k = self.params.get("smooth_k", 3)

        if not isinstance(k_period, int):
            raise ValueError(
                f"Stochastic k_period must be integer, "
                f"got: {type(k_period).__name__}"
            )

        if not isinstance(d_period, int):
            raise ValueError(
                f"Stochastic d_period must be integer, "
                f"got: {type(d_period).__name__}"
            )

        if not isinstance(smooth_k, int):
            raise ValueError(
                f"Stochastic smooth_k must be integer, "
                f"got: {type(smooth_k).__name__}"
            )

        if k_period < 1:
            raise ValueError(f"Stochastic k_period must be >= 1, got: {k_period}")

        if d_period < 1:
            raise ValueError(f"Stochastic d_period must be >= 1, got: {d_period}")

        if smooth_k < 1:
            raise ValueError(f"Stochastic smooth_k must be >= 1, got: {smooth_k}")

    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic %K and %D.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns

        Returns:
            Dict[str, pd.Series]: Dictionary with %K and %D values

        Raises:
            KeyError: If required columns missing
            ValueError: If insufficient data
        """
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(
                    f"DataFrame must have '{col}' column " f"for Stochastic calculation"
                )

        min_required = self.k_period + self.smooth_k + self.d_period
        if len(df) < min_required:
            raise ValueError(
                f"Insufficient data: need {min_required} candles, " f"got {len(df)}"
            )

        high = df["high"]
        low = df["low"]
        close = df["close"]

        lowest_low = low.rolling(window=self.k_period, min_periods=self.k_period).min()

        highest_high = high.rolling(
            window=self.k_period, min_periods=self.k_period
        ).max()

        stoch_k_raw = (close - lowest_low) / (highest_high - lowest_low) * 100

        stoch_k = stoch_k_raw.rolling(
            window=self.smooth_k, min_periods=self.smooth_k
        ).mean()

        stoch_d = stoch_k.rolling(
            window=self.d_period, min_periods=self.d_period
        ).mean()

        return {
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
        }
