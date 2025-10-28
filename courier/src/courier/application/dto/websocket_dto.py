"""
DTOs for WebSocket connections.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WebSocketConnectionInfo(BaseModel):
    """
    DTO for WebSocket connection information.

    Attributes:
        channel: Channel name
        user_id: Authenticated user ID (optional)
        wallet_address: User wallet address (optional)
        connected_at: Connection timestamp
    """

    channel: str = Field(..., description="Channel name")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    wallet_address: Optional[str] = Field(
        None, description="Wallet address (if authenticated)"
    )
    connected_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Connection timestamp (ISO format)",
    )

    @field_validator("channel")
    @classmethod
    def validate_channel_not_empty(cls, v: str) -> str:
        """Validate channel is not empty."""
        if not v or not v.strip():
            raise ValueError("Channel name cannot be empty")
        return v
