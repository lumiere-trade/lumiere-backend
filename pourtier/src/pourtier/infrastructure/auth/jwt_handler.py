"""
JWT token handler for authentication.
Provides token creation, validation, and user extraction.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict
from uuid import UUID

from jose import JWTError, jwt

from pourtier.config.settings import get_settings
from pourtier.domain.exceptions.auth import ExpiredTokenError, InvalidTokenError


def create_access_token(
    user_id: UUID, wallet_address: str, wallet_type: str = "Unknown"
) -> str:
    """
    Create JWT access token for authenticated user.

    Args:
        user_id: User UUID
        wallet_address: Solana wallet address
        wallet_type: Wallet application type (Phantom, Backpack, etc.)

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(
        ...     user_id=UUID("..."),
        ...     wallet_address="ABC123...",
        ...     wallet_type="Phantom"
        ... )
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=get_settings().JWT_EXPIRATION_HOURS)
    payload = {
        "sub": str(user_id),
        "wallet": wallet_address,
        "wallet_type": wallet_type,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(
        payload, get_settings().JWT_SECRET_KEY, algorithm=get_settings().JWT_ALGORITHM
    )
    return token


def decode_access_token(token: str) -> Dict[str, str]:
    """
    Decode and validate JWT access token.

    Args:
        token: JWT token string

    Returns:
        Dictionary with decoded payload (user_id, wallet_address, wallet_type)

    Raises:
        ExpiredTokenError: If token has expired
        InvalidTokenError: If token is invalid or malformed

    Example:
        >>> payload = decode_access_token("eyJhbG...")
        >>> payload["user_id"]
        >>> payload["wallet_address"]
        >>> payload["wallet_type"]
    """
    print(f"[JWT-DEBUG] Attempting to decode token: {token[:50]}...")
    print(f"[JWT-DEBUG] JWT_SECRET_KEY: {get_settings().JWT_SECRET_KEY}")
    print(f"[JWT-DEBUG] JWT_ALGORITHM: {get_settings().JWT_ALGORITHM}")
    
    try:
        payload = jwt.decode(
            token,
            get_settings().JWT_SECRET_KEY,
            algorithms=[get_settings().JWT_ALGORITHM],
        )
        print(f"[JWT-DEBUG] Token decoded successfully: {payload}")
        
        user_id = payload.get("sub")
        wallet = payload.get("wallet")
        
        if not user_id or not wallet:
            print(f"[JWT-DEBUG] Missing fields - user_id: {user_id}, wallet: {wallet}")
            raise InvalidTokenError()
            
        return {
            "user_id": user_id,
            "wallet_address": wallet,
            "wallet_type": payload.get("wallet_type", "Unknown"),
        }
    except jwt.ExpiredSignatureError as e:
        print(f"[JWT-DEBUG] Token expired: {e}")
        raise ExpiredTokenError()
    except JWTError as e:
        print(f"[JWT-DEBUG] JWT decode error: {type(e).__name__}: {e}")
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


def extract_wallet_type(token: str) -> str:
    """
    Extract wallet type from token.

    Args:
        token: JWT token string

    Returns:
        Wallet type string

    Raises:
        InvalidTokenError: If token is invalid

    Example:
        >>> wallet_type = extract_wallet_type(token)
    """
    payload = decode_access_token(token)
    return payload["wallet_type"]
