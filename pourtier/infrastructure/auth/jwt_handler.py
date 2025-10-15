"""
JWT token handler for authentication.

Provides token creation, validation, and user extraction.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict
from uuid import UUID

from jose import JWTError, jwt

from pourtier.config.settings import settings
from pourtier.domain.exceptions.auth import ExpiredTokenError, InvalidTokenError


def create_access_token(user_id: UUID, wallet_address: str) -> str:
    """
    Create JWT access token for authenticated user.

    Args:
        user_id: User UUID
        wallet_address: Solana wallet address

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(
        ...     user_id=UUID("..."),
        ...     wallet_address="ABC123..."
        ... )
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    payload = {
        "sub": str(user_id),  # Subject (standard JWT claim)
        "wallet": wallet_address,
        "iat": now,  # Issued at
        "exp": expire,  # Expiration time
        "type": "access",  # Token type
    }

    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_access_token(token: str) -> Dict[str, str]:
    """
    Decode and validate JWT access token.

    Args:
        token: JWT token string

    Returns:
        Dictionary with decoded payload (user_id, wallet_address)

    Raises:
        ExpiredTokenError: If token has expired
        InvalidTokenError: If token is invalid or malformed

    Example:
        >>> payload = decode_access_token("eyJhbG...")
        >>> payload["user_id"]  # UUID string
        >>> payload["wallet_address"]  # Wallet string
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Validate required fields
        user_id = payload.get("sub")
        wallet = payload.get("wallet")

        if not user_id or not wallet:
            raise InvalidTokenError()

        return {"user_id": user_id, "wallet_address": wallet}

    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError()
    except JWTError:
        raise InvalidTokenError()


def verify_token(token: str) -> bool:
    """
    Verify if token is valid without decoding payload.

    Args:
        token: JWT token string

    Returns:
        True if valid, False otherwise

    Example:
        >>> if verify_token(token):
        ...     print("Valid token")
    """
    try:
        decode_access_token(token)
        return True
    except (ExpiredTokenError, InvalidTokenError):
        return False


def extract_user_id(token: str) -> UUID:
    """
    Extract user ID from token.

    Args:
        token: JWT token string

    Returns:
        User UUID

    Raises:
        InvalidTokenError: If token is invalid

    Example:
        >>> user_id = extract_user_id(token)
    """
    payload = decode_access_token(token)
    return UUID(payload["user_id"])


def extract_wallet_address(token: str) -> str:
    """
    Extract wallet address from token.

    Args:
        token: JWT token string

    Returns:
        Wallet address string

    Raises:
        InvalidTokenError: If token is invalid

    Example:
        >>> wallet = extract_wallet_address(token)
    """
    payload = decode_access_token(token)
    return payload["wallet_address"]
