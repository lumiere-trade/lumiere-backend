"""
Authentication middleware for JWT token validation.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.di.container import get_container
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions.auth import ExpiredTokenError, InvalidTokenError
from pourtier.infrastructure.auth.jwt_handler import decode_access_token

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extract and load current authenticated user from JWT token.

    Clean architecture: Presentation depends on DI layer for dependencies,
    not on Infrastructure concrete implementations.

    Args:
        credentials: HTTP Authorization header with Bearer token
        session: Database session from dependency injection

    Returns:
        User domain entity

    Raises:
        HTTPException: 401 if token invalid, expired, or user not found
    """
    token = credentials.credentials

    try:
        # Decode JWT token - fast cryptographic operation
        payload = decode_access_token(token)
        user_id = UUID(payload["user_id"])

        # Get repository and load user
        container = get_container()
        user_repo = container.get_user_repository(session)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except ExpiredTokenError:
        # Token has expired - return 401 immediately
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        # Token is invalid or malformed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        # Invalid UUID format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception:
        # Unexpected errors - log but don't expose details
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> UUID:
    """
    Extract only user_id from authenticated user.

    Convenience dependency for endpoints that only need user ID.

    Args:
        current_user: Current user entity from get_current_user

    Returns:
        User UUID
    """
    return current_user.id


async def get_current_wallet(
    current_user: User = Depends(get_current_user),
) -> str:
    """
    Extract only wallet_address from authenticated user.

    Convenience dependency for endpoints that only need wallet address.

    Args:
        current_user: Current user entity from get_current_user

    Returns:
        Wallet address string
    """
    return current_user.wallet_address
