"""
FastAPI dependencies for Courier API.

Provides dependency injection for routes.
"""

from fastapi import Depends, HTTPException, Query, WebSocket, status
from typing import Optional

from courier.di import Container
from courier.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)

# Global container (initialized in Main.py)
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get DI container instance.

    Returns:
        Container instance

    Raises:
        RuntimeError: If container not initialized
    """
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container


def set_container(container: Container) -> None:
    """
    Set DI container (called from Main.py).

    Args:
        container: Container instance to set globally
    """
    global _container
    _container = container


async def authenticate_websocket(
    websocket: WebSocket,
    channel: str,
    token: Optional[str] = Query(None),
    container: Container = Depends(get_container),
) -> Optional[any]:
    """
    Authenticate WebSocket connection.

    Dependency that verifies JWT token and channel access.
    Closes WebSocket connection on authentication failure.

    Args:
        websocket: WebSocket connection
        channel: Channel name to access
        token: Optional JWT token from query parameter
        container: DI container

    Returns:
        TokenPayload if authenticated, None if auth not required

    Raises:
        HTTPException: On authentication/authorization failure
    """
    # If auth not required, return None
    if not container.settings.require_auth:
        return None

    # Get authentication use case
    auth_use_case = container.get_authenticate_use_case()
    if auth_use_case is None:
        return None

    # Authenticate
    try:
        return auth_use_case.execute(token, channel)
    except TokenExpiredError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token expired"
        )
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION,
            detail=str(e)
        )
    except TokenInvalidError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid token"
        )
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION,
            detail=str(e)
        )
    except AuthorizationError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Unauthorized access to channel: {channel}"
        )
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION,
            detail=str(e)
        )
    except AuthenticationError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION,
            detail=str(e)
        )
