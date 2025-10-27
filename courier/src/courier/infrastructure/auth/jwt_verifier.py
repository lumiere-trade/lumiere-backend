"""
JWT verification infrastructure for Courier.

Handles JWT token validation and channel access authorization.
"""

import jwt
from typing import Optional

from courier.domain.auth import TokenPayload


class JWTVerifier:
    """
    JWT token verifier and channel access authorizer.

    Verifies JWT tokens from WebSocket clients and checks if users
    are authorized to access specific channels.

    Attributes:
        secret: JWT secret key for verification
        algorithm: JWT algorithm (default: HS256)
    """

    def __init__(self, secret: str, algorithm: str = "HS256"):
        """
        Initialize JWT verifier.

        Args:
            secret: JWT secret key
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret = secret
        self.algorithm = algorithm

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify JWT token and return payload.

        Args:
            token: JWT token string

        Returns:
            Validated TokenPayload

        Raises:
            ValueError: If token is expired or invalid
        """
        try:
            payload = jwt.decode(
                token, self.secret, algorithms=[self.algorithm]
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def verify_channel_access(self, user_id: str, channel: str) -> bool:
        """
        Verify user can access channel.

        Authorization rules:
        - global: Everyone can access
        - user.{user_id}: Only matching user can access
        - strategy.{id}: Allow access (ownership check TODO)
        - backtest.{id}: Ephemeral, allow access
        - forge.job.{id}: Ephemeral, allow access
        - Public channels: Allow access

        Args:
            user_id: User ID from JWT token
            channel: Channel name to access

        Returns:
            True if authorized, False otherwise
        """
        # Global channel - everyone can read
        if channel == "global":
            return True

        # User channel - must match user_id
        if channel.startswith("user."):
            parts = channel.split(".", 1)
            if len(parts) == 2:
                channel_user_id = parts[1]
                return channel_user_id == user_id
            return False

        # Strategy channel - allow access for now
        # TODO: Query Architect to verify strategy ownership
        if channel.startswith("strategy."):
            return True

        # Backtest channel - ephemeral, allow access
        if channel.startswith("backtest."):
            return True

        # Forge job channel - ephemeral, allow access
        if channel.startswith("forge.job."):
            return True

        # Public channels - allow access
        if channel in [
            "trade",
            "candles",
            "sys",
            "rsi",
            "extrema",
            "analysis",
            "subscription",
            "payment",
            "deposit",
        ]:
            return True

        # Unknown channel - deny by default
        return False
