"""
Pattern recognition indicator using TA-Lib.

Detects candlestick patterns and generates aggregate scores.
Pure calculation with zero dependencies except pandas and talib.
"""

from typing import Dict, Union

import pandas as pd

from shared.indicators.base import BaseIndicator


class PatternIndicator(BaseIndicator):
    """
    Candlestick pattern recognition using TA-Lib.

    Detects multiple bullish/bearish patterns and aggregates them into scores.

    Parameters:
        bullish (list): List of bullish pattern names (e.g., ['CDLHAMMER'])
        bearish (list): List of bearish pattern names (e.g., ['CDLSHOOTINGSTAR'])
        lookback_window (int): Candles to check for patterns (default: 5)
        aggregate_method (str): Aggregation method - 'weighted_sum', 'simple_sum', 'count'

    Example:
        >>> patterns = PatternIndicator(
        ...     bullish=['CDLHAMMER', 'CDLENGULFING'],
        ...     bearish=['CDLSHOOTINGSTAR', 'CDLDARKCLOUDCOVER'],
        ...     aggregate_method='weighted_sum'
        ... )
        >>> result = patterns.calculate(df)
        >>> print(result.iloc[-1])  # Aggregate score
    """

    def __init__(
        self,
        bullish: list = None,
        bearish: list = None,
        lookback_window: int = 5,
        aggregate_method: str = "weighted_sum",
    ):
        """
        Initialize pattern indicator.

        Args:
            bullish: List of bullish pattern names
            bearish: List of bearish pattern names
            lookback_window: Candles to check for patterns
            aggregate_method: How to combine patterns
        """
        super().__init__(
            bullish=bullish or [],
            bearish=bearish or [],
            lookback_window=lookback_window,
            aggregate_method=aggregate_method,
        )
        self.bullish_patterns = self.params["bullish"]
        self.bearish_patterns = self.params["bearish"]
        self.lookback_window = self.params["lookback_window"]
        self.aggregate_method = self.params["aggregate_method"]

    def validate_params(self) -> None:
        """
        Validate pattern parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        # Use self.params instead of self.bullish_patterns
        bullish = self.params.get("bullish", [])
        bearish = self.params.get("bearish", [])
        lookback_window = self.params.get("lookback_window", 5)
        aggregate_method = self.params.get("aggregate_method", "weighted_sum")

        if not bullish and not bearish:
            raise ValueError(
                "At least one bullish or bearish pattern must be specified"
            )

        if not isinstance(lookback_window, int) or lookback_window < 1:
            raise ValueError(
                f"lookback_window must be integer >= 1, got: {lookback_window}"
            )

        valid_methods = ["weighted_sum", "simple_sum", "count"]
        if aggregate_method not in valid_methods:
            raise ValueError(
                f"aggregate_method must be one of {valid_methods}, "
                f"got: {aggregate_method}"
            )

    def calculate(
        self, df: pd.DataFrame
    ) -> Union[pd.Series, Dict[str, Union[pd.Series, Dict]]]:
        """
        Calculate pattern recognition scores.

        Args:
            df: DataFrame with OHLC columns (open, high, low, close)

        Returns:
            Dict with 'aggregate' Series and 'individual' pattern dict

        Raises:
            ImportError: If TA-Lib not installed
            KeyError: If required columns missing
        """
        # Check for TA-Lib
        try:
            import talib
        except ImportError:
            raise ImportError(
                "TA-Lib required for pattern recognition. "
                "Install with: pip install TA-Lib"
            )

        # Validate required columns
        required = ["open", "high", "low", "close"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise KeyError(f"DataFrame missing required columns: {missing}")

        open_prices = df["open"]
        high_prices = df["high"]
        low_prices = df["low"]
        close_prices = df["close"]

        # Detect all patterns
        pattern_results = {}

        # Bullish patterns (positive values)
        for pattern_name in self.bullish_patterns:
            pattern_func = getattr(talib, pattern_name, None)
            if pattern_func is None:
                # Skip unknown patterns silently (caller can validate)
                continue

            try:
                result = pattern_func(
                    open_prices, high_prices, low_prices, close_prices
                )
                pattern_results[pattern_name] = result
            except Exception:
                # Skip failed pattern computation
                continue

        # Bearish patterns (negative values)
        for pattern_name in self.bearish_patterns:
            pattern_func = getattr(talib, pattern_name, None)
            if pattern_func is None:
                continue

            try:
                result = pattern_func(
                    open_prices, high_prices, low_prices, close_prices
                )
                # Invert bearish patterns (negative score)
                pattern_results[pattern_name] = -result
            except Exception:
                continue

        # Handle case where no patterns computed
        if not pattern_results:
            empty_series = pd.Series(0.0, index=df.index)
            return {"aggregate": empty_series, "individual": {}}

        # Aggregate patterns
        aggregate_score = self._aggregate_patterns(pattern_results, df.index)

        # Return both aggregate and individual patterns
        return {"aggregate": aggregate_score, "individual": pattern_results}

    def _aggregate_patterns(
        self, pattern_results: Dict[str, pd.Series], index: pd.Index
    ) -> pd.Series:
        """
        Aggregate multiple pattern results into single score.

        Args:
            pattern_results: Dictionary of pattern results
            index: DataFrame index

        Returns:
            Aggregated score series
        """
        if self.aggregate_method == "simple_sum":
            # Simple sum of all patterns
            aggregate = sum(pattern_results.values())

        elif self.aggregate_method == "count":
            # Count number of active patterns
            aggregate = pd.Series(0, index=index)
            for result in pattern_results.values():
                aggregate += (result != 0).astype(int)

        else:  # weighted_sum (default)
            # Weighted by pattern strength (values are -100, 0, or 100)
            aggregate = sum(pattern_results.values())
            # Normalize to -100 to 100 range
            max_possible = len(pattern_results) * 100
            if max_possible > 0:
                aggregate = (aggregate / max_possible) * 100

        return aggregate
