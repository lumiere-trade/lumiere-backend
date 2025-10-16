"""
StrategyReference value object - Immutable reference to strategy.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StrategyReference:
    """
    Value object representing a reference to a strategy in architect_db.

    Business rules:
    - Strategy ID links to architect_db.strategies.id
    - Asset configuration immutable once set
    - Used for activation requests
    """

    strategy_id: UUID
    strategy_name: str
    asset_symbol: str
    asset_interval: str

    def __post_init__(self):
        """Validate strategy reference on creation."""
        if not self.strategy_name:
            raise ValueError("Strategy name is required")

        if not self.asset_symbol:
            raise ValueError("Asset symbol is required")

        if not self.asset_interval:
            raise ValueError("Asset interval is required")

        # Validate interval format
        valid_intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
        if self.asset_interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {self.asset_interval}. "
                f"Must be one of {valid_intervals}"
            )

    def display_name(self) -> str:
        """Return display name with asset info."""
        return f"{self.strategy_name} ({self.asset_symbol}/{self.asset_interval})"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "strategy_id": str(self.strategy_id),
            "strategy_name": self.strategy_name,
            "asset_symbol": self.asset_symbol,
            "asset_interval": self.asset_interval,
        }

    def __str__(self) -> str:
        """String representation."""
        return self.display_name()

    def __eq__(self, other) -> bool:
        """Compare strategy references by ID."""
        if not isinstance(other, StrategyReference):
            return False
        return self.strategy_id == other.strategy_id

    def __hash__(self) -> int:
        """Make strategy reference hashable."""
        return hash(self.strategy_id)
