"""
ChannelName value object - immutable channel name with validation.
"""

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class ChannelName:
    """
    Value object representing a validated channel name.

    Channel naming rules:
    - Lowercase alphanumeric + dots + hyphens
    - No special characters
    - Maximum 100 characters

    Examples:
        - global
        - user.123
        - strategy.abc-def
        - forge.job.xyz-123
    """

    name: str

    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[a-z0-9.\-]+$")
    MAX_LENGTH: ClassVar[int] = 100

    def __post_init__(self):
        """Validate channel name on creation."""
        if not self.name:
            raise ValueError("Channel name cannot be empty")

        if len(self.name) > self.MAX_LENGTH:
            raise ValueError(
                f"Channel name too long (max {self.MAX_LENGTH} characters)"
            )

        if not self.PATTERN.match(self.name):
            raise ValueError(
                "Channel name must contain only lowercase letters, "
                "numbers, dots, and hyphens"
            )

    @property
    def value(self) -> str:
        """Get channel name value."""
        return self.name

    def is_global(self) -> bool:
        """Check if this is the global channel."""
        return self.name == "global"

    def is_user_channel(self) -> bool:
        """Check if this is a user-specific channel."""
        return self.name.startswith("user.")

    def is_strategy_channel(self) -> bool:
        """Check if this is a strategy channel."""
        return self.name.startswith("strategy.")

    def is_ephemeral(self) -> bool:
        """Check if this is an ephemeral channel (forge jobs, backtests)."""
        return self.name.startswith(("forge.job.", "backtest."))

    def extract_user_id(self) -> str:
        """
        Extract user ID from user channel name.

        Returns:
            User ID if this is a user channel

        Raises:
            ValueError: If not a user channel
        """
        if not self.is_user_channel():
            raise ValueError(f"Not a user channel: {self.name}")
        return self.name.split(".", 1)[1]

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ChannelName({self.name!r})"
