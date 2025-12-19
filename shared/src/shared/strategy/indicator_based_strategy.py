"""
Indicator-based Trading Strategy.

Extends TradingStrategy with indicator-specific helper methods
for TSDL v2 indicator_based plugin.
"""

from typing import Any

from shared.strategy.base_strategy import TradingStrategy


class IndicatorBasedStrategy(TradingStrategy):
    """Strategy with indicator-specific helper methods.

    Adds support for trend and pattern detection operators:
    - rising/falling - simple trend detection
    - rising_for/falling_for - sustained trend detection
    - divergence_bullish/divergence_bearish - divergence detection
    """

    def _is_rising(self, indicator_name: str, current_value: Any) -> bool:
        """Check if indicator is rising (current > previous).

        Args:
            indicator_name: Name of the indicator
            current_value: Current value of the indicator

        Returns:
            True if current value > previous value
        """
        prev_value = self._get_previous_value(indicator_name, None)

        if prev_value is None:
            return False

        try:
            return current_value > prev_value
        except (TypeError, ValueError):
            return False

    def _is_falling(self, indicator_name: str, current_value: Any) -> bool:
        """Check if indicator is falling (current < previous).

        Args:
            indicator_name: Name of the indicator
            current_value: Current value of the indicator

        Returns:
            True if current value < previous value
        """
        prev_value = self._get_previous_value(indicator_name, None)

        if prev_value is None:
            return False

        try:
            return current_value < prev_value
        except (TypeError, ValueError):
            return False

    def _is_rising_for(
        self, indicator_name: str, current_value: Any, periods: int
    ) -> bool:
        """Check if indicator has been rising for N periods.

        Args:
            indicator_name: Name of the indicator
            current_value: Current value of the indicator
            periods: Number of consecutive periods to check

        Returns:
            True if indicator has been rising for specified periods
        """
        if indicator_name not in self._indicator_history:
            return False

        history = self._indicator_history[indicator_name]

        # Need N+1 values to check N periods of rising
        if len(history) < periods + 1:
            return False

        try:
            # Get last N+1 values (including current)
            recent_values = history[-(periods + 1) :]

            # Check each period is higher than previous
            for i in range(1, len(recent_values)):
                if recent_values[i] <= recent_values[i - 1]:
                    return False

            return True
        except (TypeError, ValueError, IndexError):
            return False

    def _is_falling_for(
        self, indicator_name: str, current_value: Any, periods: int
    ) -> bool:
        """Check if indicator has been falling for N periods.

        Args:
            indicator_name: Name of the indicator
            current_value: Current value of the indicator
            periods: Number of consecutive periods to check

        Returns:
            True if indicator has been falling for specified periods
        """
        if indicator_name not in self._indicator_history:
            return False

        history = self._indicator_history[indicator_name]

        # Need N+1 values to check N periods of falling
        if len(history) < periods + 1:
            return False

        try:
            # Get last N+1 values (including current)
            recent_values = history[-(periods + 1) :]

            # Check each period is lower than previous
            for i in range(1, len(recent_values)):
                if recent_values[i] >= recent_values[i - 1]:
                    return False

            return True
        except (TypeError, ValueError, IndexError):
            return False

    def _divergence_bullish(
        self,
        price_name: str,
        indicator_name: str,
        current_price: Any,
        current_indicator: Any,
        lookback: int = 14,
    ) -> bool:
        """Check for bullish divergence (price lower low, indicator higher low).

        Args:
            price_name: Name of price field (e.g., 'CLOSE')
            indicator_name: Name of indicator
            current_price: Current price value
            current_indicator: Current indicator value
            lookback: Periods to look back for lows

        Returns:
            True if bullish divergence detected
        """
        if price_name not in self._indicator_history:
            return False
        if indicator_name not in self._indicator_history:
            return False

        price_history = self._indicator_history[price_name]
        indicator_history = self._indicator_history[indicator_name]

        if len(price_history) < lookback or len(indicator_history) < lookback:
            return False

        try:
            # Find previous low in price
            recent_prices = price_history[-lookback:]
            prev_price_low = min(recent_prices[:-1])  # Exclude current

            # Find previous low in indicator
            recent_indicators = indicator_history[-lookback:]
            prev_indicator_low = min(recent_indicators[:-1])  # Exclude current

            # Bullish divergence: price makes lower low, indicator makes higher low
            price_lower_low = current_price < prev_price_low
            indicator_higher_low = current_indicator > prev_indicator_low

            return price_lower_low and indicator_higher_low
        except (TypeError, ValueError, IndexError):
            return False

    def _divergence_bearish(
        self,
        price_name: str,
        indicator_name: str,
        current_price: Any,
        current_indicator: Any,
        lookback: int = 14,
    ) -> bool:
        """Check for bearish divergence (price higher high, indicator lower high).

        Args:
            price_name: Name of price field (e.g., 'CLOSE')
            indicator_name: Name of indicator
            current_price: Current price value
            current_indicator: Current indicator value
            lookback: Periods to look back for highs

        Returns:
            True if bearish divergence detected
        """
        if price_name not in self._indicator_history:
            return False
        if indicator_name not in self._indicator_history:
            return False

        price_history = self._indicator_history[price_name]
        indicator_history = self._indicator_history[indicator_name]

        if len(price_history) < lookback or len(indicator_history) < lookback:
            return False

        try:
            # Find previous high in price
            recent_prices = price_history[-lookback:]
            prev_price_high = max(recent_prices[:-1])  # Exclude current

            # Find previous high in indicator
            recent_indicators = indicator_history[-lookback:]
            prev_indicator_high = max(recent_indicators[:-1])  # Exclude current

            # Bearish divergence: price makes higher high, indicator makes lower high
            price_higher_high = current_price > prev_price_high
            indicator_lower_high = current_indicator < prev_indicator_high

            return price_higher_high and indicator_lower_high
        except (TypeError, ValueError, IndexError):
            return False

    def _crosses_above(
        self,
        left_name: str,
        right_name: str,
        current_left: Any,
        current_right: Any,
    ) -> bool:
        """Check if left indicator crosses above right indicator.

        Args:
            left_name: Name of left indicator
            right_name: Name of right indicator
            current_left: Current value of left indicator
            current_right: Current value of right indicator

        Returns:
            True if left crosses above right (was below, now above)
        """
        prev_left = self._get_previous_value(left_name, None)
        prev_right = self._get_previous_value(right_name, None)

        if prev_left is None or prev_right is None:
            return False

        try:
            was_below = prev_left <= prev_right
            now_above = current_left > current_right
            return was_below and now_above
        except (TypeError, ValueError):
            return False

    def _crosses_below(
        self,
        left_name: str,
        right_name: str,
        current_left: Any,
        current_right: Any,
    ) -> bool:
        """Check if left indicator crosses below right indicator.

        Args:
            left_name: Name of left indicator
            right_name: Name of right indicator
            current_left: Current value of left indicator
            current_right: Current value of right indicator

        Returns:
            True if left crosses below right (was above, now below)
        """
        prev_left = self._get_previous_value(left_name, None)
        prev_right = self._get_previous_value(right_name, None)

        if prev_left is None or prev_right is None:
            return False

        try:
            was_above = prev_left >= prev_right
            now_below = current_left < current_right
            return was_above and now_below
        except (TypeError, ValueError):
            return False
