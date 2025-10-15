"""
Trading operations and position management emoji definitions.

Covers position entry/exit, swaps, PNL tracking, and risk management.

Usage:
    >>> from shared.reporter.emojis.trading import TradingEmoji
    >>> print(f"{TradingEmoji.BUY} Opened long position")
    🟢 Opened long position
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class TradingEmoji(ComponentEmoji):
    """
    Trading operations, positions, and signals.

    Categories:
        - Positions: Entry, exit, management
        - Outcomes: Profit, loss, breakeven
        - Operations: Swaps, transfers, balances
        - Signals: Entry/exit signals
        - Risk: Stop loss, take profit
    """

    # ============================================================
    # Position Management
    # ============================================================

    BUY = "🟢"  # Open long position / Buy signal
    SELL = "🔴"  # Close position / Sell signal
    POSITION_OPEN = "📈"  # Position opened
    POSITION_CLOSE = "📉"  # Position closed
    POSITION_INFO = "📊"  # Position information

    # ============================================================
    # Trade Outcomes
    # ============================================================

    PROFIT = "💰"  # Profitable trade
    LOSS = "📉"  # Losing trade
    BREAKEVEN = "➖"  # Breakeven trade
    BIG_WIN = "🎉"  # Large profit
    BIG_LOSS = "😱"  # Large loss

    # ============================================================
    # DEX Operations
    # ============================================================

    SWAP = "🔄"  # Token swap on DEX
    SWAP_SUCCESS = "💱"  # Swap completed successfully
    SWAP_PENDING = "⏳"  # Swap pending
    SWAP_FAILED = "❌"  # Swap failed

    # ============================================================
    # Balance & Portfolio
    # ============================================================

    BALANCE = "💼"  # Balance query/check
    BALANCE_LOW = "⚠️"  # Low balance warning
    BALANCE_OK = "✅"  # Balance sufficient
    TRANSFER = "💸"  # Token transfer
    WALLET = "👛"  # Wallet operation

    # ============================================================
    # Signals & Analysis
    # ============================================================

    SIGNAL = "🎯"  # Trading signal generated
    ENTRY_SIGNAL = "🚪"  # Entry point identified
    EXIT_SIGNAL = "🚶"  # Exit point identified
    STRONG_SIGNAL = "💪"  # Strong signal
    WEAK_SIGNAL = "👎"  # Weak signal

    # ============================================================
    # Risk Management
    # ============================================================

    STOP_LOSS = "🛑"  # Stop loss triggered
    TAKE_PROFIT = "🎯"  # Take profit hit
    TRAILING_STOP = "📍"  # Trailing stop updated
    RISK_WARNING = "⚠️"  # Risk warning
    HARD_STOP = "🚨"  # Hard stop triggered

    # ============================================================
    # Strategy State
    # ============================================================

    STRATEGY_START = "▶️"  # Strategy started
    STRATEGY_STOP = "⏹️"  # Strategy stopped
    STRATEGY_PAUSE = "⏸️"  # Strategy paused
    STRATEGY_RESUME = "▶️"  # Strategy resumed
