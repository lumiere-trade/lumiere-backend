"""
Authentication domain models for Courier.

Defines JWT token payload and authenticated client structures.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """
    JWT token payload structure.

    Attributes:
        user_id: Unique user identifier
        wallet_address: Solana wallet address
        exp: Token expiration timestamp (Unix epoch)
        iat: Token issued at timestamp (Unix epoch)
    """

    user_id: str = Field(..., description="User ID from database")
    wallet_address: str = Field(..., description="Solana wallet address")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")


class AuthenticatedClient(BaseModel):
    """
    Authenticated WebSocket client metadata.

    Stored for each connected client to track authorization.

    Attributes:
        user_id: Authenticated user ID
        wallet_address: User's wallet address
        channel: Channel the client is subscribed to
        connected_at: Connection timestamp (ISO format)
    """

    user_id: str = Field(..., description="User ID")
    wallet_address: str = Field(..., description="Wallet address")
    channel: str = Field(..., description="Subscribed channel")
    connected_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Connection timestamp",
    )
