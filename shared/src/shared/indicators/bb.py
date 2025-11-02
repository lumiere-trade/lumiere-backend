"""
Bollinger Bands indicator implementation.

Calculates volatility bands around a moving average.
Pure calculation with optional width and %B metrics.
"""

from typing import Dict

import pandas as pd

from shared.indicators.base import BaseIndicator


class BollingerBandsIndicator(BaseIndicator):
    """
    Bollinger Bands indicator with optional metrics.

    Calculates:
    - Middle band (SMA)
    - Upper band (middle + std * multiplier)
    - Lower band (middle - std * multiplier)
    - BB Width (volatility percentage)
    - BB %B (price position within bands, 0-1)

    Parameters:
        period (int): SMA period for middle band (default: 20)
        std_multiplier (float): Standard deviation multiplier (default: 2.0)
        compute_width (bool): Calculate BB width (default: True)
        compute_percent (bool): Calculate %B position (default: True)

    Example:
        >>> bb = BollingerBandsIndicator(period=20, std_multiplier=2.0)
        >>> result = bb.calculate(df)
        >>> print(result['middle'].iloc[-1])
        >>> print(result['upper'].iloc[-1])
        >>> print(result['bb_width'].iloc[-1])
    """

    def __init__(
        self,
        period: int = 20,
        std_multiplier: float = 2.0,
        compute_width: bool = True,
        compute_percent: bool = True,
    ):
        """
        Initialize Bollinger Bands indicator.

        Args:
            period: SMA period for middle band
            std_multiplier: Standard deviation multiplier for bands
            compute_width: Calculate BB width (volatility)
            compute_percent: Calculate %B (position in bands)
        """
        super().__init__(
            period=period,
            std_multiplier=std_multiplier,
            compute_width=compute_width,
            compute_percent=compute_percent,
        )
        self.period = self.params["period"]
        self.std_multiplier = self.params["std_multiplier"]
        self.compute_width = self.params["compute_width"]
        self.compute_percent = self.params["compute_percent"]

    def validate_params(self) -> None:
        """
        Validate Bollinger Bands parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        period = self.params.get("period", 20)
        std_multiplier = self.params.get("std_multiplier", 2.0)

        if not isinstance(period, int):
            raise ValueError(f"BB period must be integer, got: {type(period).__name__}")

        if period < 2:
            raise ValueError(f"BB period must be >= 2, got: {period}")

        if not isinstance(std_multiplier, (int, float)):
            raise ValueError(
                f"BB std_multiplier must be numeric, "
                f"got: {type(std_multiplier).__name__}"
            )

        if std_multiplier <= 0:
            raise ValueError(f"BB std_multiplier must be > 0, got: {std_multiplier}")

    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands and optional metrics.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Dict[str, pd.Series]: Dictionary with bands and metrics

        Raises:
            KeyError: If 'close' column missing
            ValueError: If insufficient data
        """
        if "close" not in df.columns:
            raise KeyError("DataFrame must have 'close' column for BB calculation")

        if len(df) < self.period:
            raise ValueError(
                f"Insufficient data: need {self.period} candles, " f"got {len(df)}"
            )

        close = df["close"]

        middle = close.rolling(window=self.period, min_periods=self.period).mean()

        std = close.rolling(window=self.period, min_periods=self.period).std()

        upper = middle + (std * self.std_multiplier)
        lower = middle - (std * self.std_multiplier)

        results = {
            "middle": middle,
            "upper": upper,
            "lower": lower,
        }

        if self.compute_width:
            bb_width = (upper - lower) / middle * 100
            results["bb_width"] = bb_width

        if self.compute_percent:
            bb_percent = (close - lower) / (upper - lower)
            results["bb_percent"] = bb_percent

        return results
