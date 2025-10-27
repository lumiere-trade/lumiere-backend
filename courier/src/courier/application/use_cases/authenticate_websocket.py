"""
Use case for authenticating WebSocket connections.
"""

from typing import Optional

from courier.domain.auth import TokenPayload
from courier.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)
from courier.domain.value_objects import ChannelName
from courier.infrastructure.auth import JWTVerifier


class AuthenticateWebSocketUseCase:
    """
    Use case for authenticating WebSocket connections.

    Verifies JWT token and checks channel access authorization.
    """

    def __init__(self, jwt_verifier: JWTVerifier):
        """
        Initialize use case.

        Args:
            jwt_verifier: JWT token verifier
        """
        self.jwt_verifier = jwt_verifier

    def execute(
        self, token: Optional[str], channel_name: str
    ) -> Optional[TokenPayload]:
        """
        Authenticate WebSocket connection.

        Args:
            token: JWT token (optional)
            channel_name: Channel to access

        Returns:
            TokenPayload if authenticated, None if no token provided

        Raises:
            AuthenticationError: If token is invalid or expired
            AuthorizationError: If user not authorized for channel
        """
        # No token provided - unauthenticated access
        if not token:
            return None

        # Verify token
        try:
            payload = self.jwt_verifier.verify_token(token)
        except ValueError as e:
            if "expired" in str(e).lower():
                raise TokenExpiredError(str(e))
            raise TokenInvalidError(str(e))

        # Validate channel name
        try:
            channel = ChannelName(channel_name)
        except ValueError as e:
            raise AuthenticationError(f"Invalid channel name: {e}")

        # Check authorization
        if not self.jwt_verifier.verify_channel_access(
            payload.user_id, channel_name
        ):
            raise AuthorizationError(
                f"User not authorized for channel: {channel_name}",
                user_id=payload.user_id,
                resource=channel_name,
            )

        return payload
