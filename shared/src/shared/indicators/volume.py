"""
Volume indicators implementation.

Calculates volume-based indicators: OBV and Volume SMA.
Pure calculation for volume analysis.
"""

from typing import Dict

import pandas as pd

from shared.indicators.base import BaseIndicator


class VolumeIndicator(BaseIndicator):
    """
    Volume indicators with OBV and Volume SMA.

    Calculates:
    - OBV (On-Balance Volume): Cumulative volume flow
    - Volume SMA: Simple moving average of volume
    - Volume ratio: Current volume / Volume SMA

    Parameters:
        sma_period (int): Period for volume SMA (default: 20)
        compute_obv (bool): Calculate OBV (default: True)
        compute_ratio (bool): Calculate volume ratio (default: True)

    Example:
        >>> vol = VolumeIndicator(sma_period=20, compute_obv=True)
        >>> result = vol.calculate(df)
        >>> print(result['obv'].iloc[-1])
        >>> print(result['volume_sma'].iloc[-1])
        >>> print(result['volume_ratio'].iloc[-1])
    """

    def __init__(
        self, sma_period: int = 20, compute_obv: bool = True, compute_ratio: bool = True
    ):
        """
        Initialize Volume indicator.

        Args:
            sma_period: Period for volume SMA
            compute_obv: Calculate OBV
            compute_ratio: Calculate volume ratio
        """
        super().__init__(
            sma_period=sma_period, compute_obv=compute_obv, compute_ratio=compute_ratio
        )
        self.sma_period = self.params["sma_period"]
        self.compute_obv = self.params["compute_obv"]
        self.compute_ratio = self.params["compute_ratio"]

    def validate_params(self) -> None:
        """
        Validate Volume indicator parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        sma_period = self.params.get("sma_period", 20)

        if not isinstance(sma_period, int):
            raise ValueError(
                f"Volume sma_period must be integer, "
                f"got: {type(sma_period).__name__}"
            )

        if sma_period < 1:
            raise ValueError(f"Volume sma_period must be >= 1, got: {sma_period}")

    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate volume indicators.

        Args:
            df: DataFrame with 'close', 'volume' columns

        Returns:
            Dict[str, pd.Series]: Dictionary with volume indicators

        Raises:
            KeyError: If required columns missing
            ValueError: If insufficient data
        """
        required_cols = ["close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(
                    f"DataFrame must have '{col}' column " f"for Volume calculation"
                )

        if len(df) < self.sma_period:
            raise ValueError(
                f"Insufficient data: need {self.sma_period} candles, " f"got {len(df)}"
            )

        close = df["close"]
        volume = df["volume"]

        volume_sma = volume.rolling(
            window=self.sma_period, min_periods=self.sma_period
        ).mean()

        results = {
            "volume_sma": volume_sma,
        }

        if self.compute_obv:
            price_direction = close.diff()
            obv = (
                volume
                * price_direction.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
            ).cumsum()
            results["obv"] = obv

        if self.compute_ratio:
            volume_ratio = volume / volume_sma
            results["volume_ratio"] = volume_ratio

        return results
