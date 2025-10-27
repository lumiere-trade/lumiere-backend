"""
ChannelName value object - immutable channel name with validation.
"""

import re
from typing import ClassVar


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

    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[a-z0-9.\-]+$")
    MAX_LENGTH: ClassVar[int] = 100

    def __init__(self, name: str):
        """
        Initialize ChannelName.

        Args:
            name: Channel name string

        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError("Channel name cannot be empty")

        if len(name) > self.MAX_LENGTH:
            raise ValueError(
                f"Channel name too long (max {self.MAX_LENGTH} characters)"
            )

        if not self.PATTERN.match(name):
            raise ValueError(
                "Channel name must contain only lowercase letters, "
                "numbers, dots, and hyphens"
            )

        self._name = name

    @property
    def value(self) -> str:
        """Get channel name value."""
        return self._name

    def is_global(self) -> bool:
        """Check if this is the global channel."""
        return self._name == "global"

    def is_user_channel(self) -> bool:
        """Check if this is a user-specific channel."""
        return self._name.startswith("user.")

    def is_strategy_channel(self) -> bool:
        """Check if this is a strategy channel."""
        return self._name.startswith("strategy.")

    def is_ephemeral(self) -> bool:
        """Check if this is an ephemeral channel (forge jobs, backtests)."""
        return self._name.startswith(("forge.job.", "backtest."))

    def extract_user_id(self) -> str:
        """
        Extract user ID from user channel name.

        Returns:
            User ID if this is a user channel

        Raises:
            ValueError: If not a user channel
        """
        if not self.is_user_channel():
            raise ValueError(f"Not a user channel: {self._name}")
        return self._name.split(".", 1)[1]

    def __eq__(self, other) -> bool:
        """Check equality."""
        if isinstance(other, ChannelName):
            return self._name == other._name
        return False

    def __hash__(self) -> int:
        """Hash based on name."""
        return hash(self._name)

    def __str__(self) -> str:
        """String representation."""
        return self._name

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ChannelName({self._name!r})"
