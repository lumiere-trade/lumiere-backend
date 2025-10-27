"""
Message value object - immutable message with validation.
"""

from datetime import datetime
from typing import Any, Dict


class Message:
    """
    Value object representing a message to be broadcast.

    Messages are immutable once created.

    Attributes:
        data: Message payload (dict)
        timestamp: Message creation timestamp
    """

    def __init__(self, data: Dict[str, Any], timestamp: datetime = None):
        """
        Initialize Message.

        Args:
            data: Message payload
            timestamp: Optional timestamp (defaults to now)

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Message data must be a dictionary")

        if not data:
            raise ValueError("Message data cannot be empty")

        self._data = data.copy()
        self._timestamp = timestamp or datetime.utcnow()

    @property
    def data(self) -> Dict[str, Any]:
        """Get message data (immutable copy)."""
        return self._data.copy()

    @property
    def timestamp(self) -> datetime:
        """Get message timestamp."""
        return self._timestamp

    def get_type(self) -> str:
        """
        Get message type.

        Returns:
            Message type string, or 'unknown' if not specified
        """
        return self._data.get("type", "unknown")

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"Message(type={self.get_type()}, "
            f"timestamp={self._timestamp.isoformat()})"
        )
