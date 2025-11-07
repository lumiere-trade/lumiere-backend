"""
Authentication middleware for JWT token validation.
"""

import traceback
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.di.container import get_container
from pourtier.di.dependencies import get_db_session
from pourtier.domain.entities.user import User
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
    print(f"[AUTH-DEBUG] get_current_user called!")
    print(f"[AUTH-DEBUG] credentials: {credentials}")

    token = credentials.credentials
    print(f"[AUTH-DEBUG] token: {token[:50]}...")

    try:
        # Decode JWT token
        print(f"[AUTH-DEBUG] Step 1: Decoding JWT token...")
        payload = decode_access_token(token)
        print(f"[AUTH-DEBUG] Step 1 DONE: Payload decoded")

        print(f"[AUTH-DEBUG] Step 2: Extracting user_id from payload...")
        user_id = UUID(payload["user_id"])
        print(f"[AUTH-DEBUG] Step 2 DONE: Extracted user_id: {user_id}")

        # Get repository instance from container with session
        print(f"[AUTH-DEBUG] Step 3: Getting container...")
        container = get_container()
        print(f"[AUTH-DEBUG] Step 3 DONE: Got container: {container}")

        print(f"[AUTH-DEBUG] Step 4: Getting user repository...")
        user_repo = container.get_user_repository(session)
        print(f"[AUTH-DEBUG] Step 4 DONE: Got user_repo: {user_repo}")

        # Load user from database
        print(f"[AUTH-DEBUG] Step 5: Fetching user from database with id={user_id}...")
        user = await user_repo.get_by_id(user_id)
        print(f"[AUTH-DEBUG] Step 5 DONE: User fetched: {user}")

        if not user:
            print(f"[AUTH-DEBUG] User not found in database!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        print(f"[AUTH-DEBUG] Returning user: {user.id} - {user.wallet_address}")
        return user

    except ValueError as e:
        # Invalid UUID or token format
        print(f"[AUTH-DEBUG] ValueError: {e}")
        print(f"[AUTH-DEBUG] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        print(f"[AUTH-DEBUG] HTTPException caught, re-raising...")
        raise
    except Exception as e:
        # Unexpected errors
        print(f"[AUTH-DEBUG] Unexpected error: {type(e).__name__}: {e}")
        print(f"[AUTH-DEBUG] Traceback: {traceback.format_exc()}")
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
