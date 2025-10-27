"""
Channel-related exceptions.
"""


class ChannelError(Exception):
    """Base exception for channel errors."""

    pass


class ChannelNotFoundError(ChannelError):
    """Raised when channel does not exist."""

    def __init__(self, channel_name: str):
        """
        Initialize ChannelNotFoundError.

        Args:
            channel_name: Name of channel that was not found
        """
        super().__init__(f"Channel not found: {channel_name}")
        self.channel_name = channel_name


class InvalidChannelNameError(ChannelError):
    """Raised when channel name is invalid."""

    def __init__(self, channel_name: str, reason: str):
        """
        Initialize InvalidChannelNameError.

        Args:
            channel_name: Invalid channel name
            reason: Reason why name is invalid
        """
        super().__init__(f"Invalid channel name '{channel_name}': {reason}")
        self.channel_name = channel_name
        self.reason = reason
