"""
Technical indicators and market analysis emoji definitions.

Covers RSI, moving averages, patterns, trends, and market conditions.

Usage:
    >>> from shared.reporter.emojis.indicators import IndicatorEmoji
    >>> print(f"{IndicatorEmoji.RSI} RSI: 65.5")
    📊 RSI: 65.5
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class IndicatorEmoji(ComponentEmoji):
    """
    Technical indicators and market analysis.

    Categories:
        - Indicators: RSI, EMA, SMA, MACD
        - Patterns: Chart patterns, candle patterns
        - Trends: Uptrend, downtrend, sideways
        - Market: Bullish, bearish, volatile
    """

    # ============================================================
    # Specific Indicators
    # ============================================================

    RSI = "📊"  # Relative Strength Index
    EMA = "📈"  # Exponential Moving Average
    SMA = "📉"  # Simple Moving Average
    MACD = "〰️"  # Moving Average Convergence Divergence
    BOLLINGER = "📏"  # Bollinger Bands
    VOLUME = "📊"  # Volume indicator

    # ============================================================
    # Pattern Detection
    # ============================================================

    PATTERN = "🔉"  # Pattern detected
    CANDLE = "🕯️"  # Candle pattern
    CHART_PATTERN = "📐"  # Chart pattern
    FORMATION = "🔺"  # Formation detected

    # ============================================================
    # Trend Analysis
    # ============================================================

    TREND_UP = "⬆️"  # Uptrend detected
    TREND_DOWN = "⬇️"  # Downtrend detected
    TREND_NEUTRAL = "➡️"  # Sideways/neutral trend
    TREND_CHANGE = "🔀"  # Trend change detected
    REVERSAL = "↩️"  # Trend reversal

    # ============================================================
    # Market Conditions
    # ============================================================

    BULLISH = "🐂"  # Bullish market
    BEARISH = "🐻"  # Bearish market
    VOLATILE = "🌊"  # High volatility
    CONSOLIDATION = "📦"  # Price consolidation
    BREAKOUT = "💥"  # Price breakout

    # ============================================================
    # Signal Strength
    # ============================================================

    STRONG_SIGNAL = "💪"  # Strong indicator signal
    WEAK_SIGNAL = "👎"  # Weak indicator signal
    DIVERGENCE = "🔀"  # Indicator divergence
    CONFIRMATION = "✔️"  # Signal confirmation

    # ============================================================
    # Indicator State
    # ============================================================

    OVERBOUGHT = "🔴"  # Overbought condition
    OVERSOLD = "🟢"  # Oversold condition
    NEUTRAL = "🟡"  # Neutral condition
    WARMING_UP = "🔥"  # Indicator warming up
    READY = "✅"  # Indicator ready
