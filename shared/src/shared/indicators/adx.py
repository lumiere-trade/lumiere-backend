"""
ADX (Average Directional Index) indicator implementation.

Measures trend strength regardless of direction.
ADX > 25 indicates strong trend, < 20 indicates weak/ranging.
"""

from typing import Dict, Union

import pandas as pd

from shared.indicators.base import BaseIndicator


class ADXIndicator(BaseIndicator):
    """
    ADX indicator for trend strength measurement.

    Calculates:
    - +DI (Positive Directional Indicator)
    - -DI (Negative Directional Indicator)
    - ADX (Average Directional Index)

    Parameters:
        period (int): Smoothing period for DI and ADX (default: 14)
        return_components (bool): Return +DI, -DI along with ADX (default: False)

    Example:
        >>> adx = ADXIndicator(period=14)
        >>> result = adx.calculate(df)
        >>> print(result.iloc[-1])  # ADX value

        >>> adx = ADXIndicator(period=14, return_components=True)
        >>> result = adx.calculate(df)
        >>> print(result['adx'].iloc[-1])
        >>> print(result['plus_di'].iloc[-1])
        >>> print(result['minus_di'].iloc[-1])
    """

    def __init__(self, period: int = 14, return_components: bool = False):
        """
        Initialize ADX indicator.

        Args:
            period: Smoothing period (number of candles)
            return_components: Return +DI and -DI components
        """
        super().__init__(period=period, return_components=return_components)
        self.period = self.params["period"]
        self.return_components = self.params["return_components"]

    def validate_params(self) -> None:
        """
        Validate ADX parameters.

        Raises:
            ValueError: If period is not integer >= 2
        """
        period = self.params.get("period", 14)

        if not isinstance(period, int):
            raise ValueError(
                f"ADX period must be integer, got: {type(period).__name__}"
            )

        if period < 2:
            raise ValueError(f"ADX period must be >= 2, got: {period}")

    def calculate(self, df: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate ADX and optional directional indicators.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns

        Returns:
            pd.Series: If only ADX requested
            Dict[str, pd.Series]: If components requested

        Raises:
            KeyError: If required columns missing
            ValueError: If insufficient data
        """
        # Validate DataFrame
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(
                    f"DataFrame must have '{col}' column for ADX calculation"
                )

        if len(df) < self.period * 2:
            raise ValueError(
                f"Insufficient data: need {self.period * 2} candles, " f"got {len(df)}"
            )

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()

        # Set DM to 0 if movement is not directional
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0

        # Smooth TR and DM using Wilder's smoothing
        atr = self._wilders_smoothing(tr, self.period)
        plus_di_smooth = self._wilders_smoothing(plus_dm, self.period)
        minus_di_smooth = self._wilders_smoothing(minus_dm, self.period)

        # Calculate +DI and -DI
        plus_di = 100 * (plus_di_smooth / atr)
        minus_di = 100 * (minus_di_smooth / atr)

        # Calculate DX (Directional Index)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))

        # Calculate ADX (smoothed DX)
        adx = self._wilders_smoothing(dx, self.period)

        # Return based on configuration
        if not self.return_components:
            return adx

        return {
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
        }

    def _wilders_smoothing(self, series: pd.Series, period: int) -> pd.Series:
        """
        Apply Wilder's smoothing (modified EMA).

        Args:
            series: Series to smooth
            period: Smoothing period

        Returns:
            Smoothed series
        """
        alpha = 1.0 / period
        return series.ewm(alpha=alpha, adjust=False).mean()
