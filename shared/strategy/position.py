"""
Position Entity.

Represents an open or closed trading position.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from shared.strategy.enums import PositionSide, PositionStatus


class Position:
    """Trading position entity."""

    def __init__(
        self,
        position_id: str,
        symbol: str,
        side: PositionSide,
        entry_price: float,
        size: float,
        entry_time: datetime,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize position."""
        self.position_id = position_id
        self.symbol = symbol
        self.side = side
        self.entry_price = float(entry_price)
        self.size = float(size)
        self.entry_time = entry_time
        self.stop_loss = float(stop_loss) if stop_loss else None
        self.take_profit = float(take_profit) if take_profit else None
        self.trailing_stop = float(trailing_stop) if trailing_stop else None
        self.metadata = metadata or {}
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None
        self.status: PositionStatus = PositionStatus.OPEN
        self.realized_pnl: Optional[float] = None
        self.highest_price: float = entry_price
        self.lowest_price: float = entry_price

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL."""
        current_price = float(current_price)
        if self.side == PositionSide.LONG:
            pnl = (current_price - self.entry_price) * self.size
        else:
            pnl = (self.entry_price - current_price) * self.size
        return pnl

    def should_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss should trigger."""
        if self.stop_loss is None:
            return False
        current_price = float(current_price)
        if self.side == PositionSide.LONG:
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss

    def should_take_profit(self, current_price: float) -> bool:
        """Check if take profit should trigger."""
        if self.take_profit is None:
            return False
        current_price = float(current_price)
        if self.side == PositionSide.LONG:
            return current_price >= self.take_profit
        else:
            return current_price <= self.take_profit

    def update_price(self, current_price: float) -> None:
        """Update position with current market price."""
        current_price = float(current_price)
        if current_price > self.highest_price:
            self.highest_price = current_price
        if current_price < self.lowest_price:
            self.lowest_price = current_price
        if self.trailing_stop and self.side == PositionSide.LONG:
            new_stop = self.highest_price * (1 - self.trailing_stop / 100)
            if self.stop_loss is None or new_stop > self.stop_loss:
                self.stop_loss = new_stop
        elif self.trailing_stop and self.side == PositionSide.SHORT:
            new_stop = self.lowest_price * (1 + self.trailing_stop / 100)
            if self.stop_loss is None or new_stop < self.stop_loss:
                self.stop_loss = new_stop

    def close(self, exit_price: float, exit_time: datetime) -> float:
        """Close the position."""
        self.exit_price = float(exit_price)
        self.exit_time = exit_time
        self.status = PositionStatus.CLOSED
        self.realized_pnl = self.calculate_unrealized_pnl(exit_price)
        return self.realized_pnl

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Position(id={self.position_id}, symbol={self.symbol}, "
            f"side={self.side}, size={self.size}, "
            f"entry={self.entry_price}, status={self.status})"
        )
