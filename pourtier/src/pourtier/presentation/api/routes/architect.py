"""
Architect Proxy Routes.

Forwards strategy/conversation requests to Architect with X-User-ID header.
Frontend → Pourtier (JWT validation) → Architect (X-User-ID)
"""

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

router = APIRouter(prefix="/architect", tags=["architect"])


async def _forward_to_architect(
    method: str,
    path: str,
    user_id: UUID,
    settings: Settings,
    body: Optional[dict] = None,
    query: Optional[dict] = None,
) -> tuple[int, Optional[dict]]:
    """
    Forward request to Architect with X-User-ID header.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        path: Architect API path (e.g., /api/strategies)
        user_id: Current user ID from JWT token
        settings: Application settings
        body: Optional request body (JSON)
        query: Optional query parameters

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If Architect request fails
    """
    architect_url = settings.ARCHITECT_URL
    url = f"{architect_url}{path}"

    headers = {
        "X-User-ID": str(user_id),
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                params=query,
            )

            # Handle 204 No Content
            if response.status_code == 204:
                return (204, None)

            # Forward status code and body
            response_data = None
            if response.text:
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"detail": response.text}

            # If not successful, raise HTTPException with Architect's error
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=(
                        response_data.get("detail", "Architect request failed")
                        if response_data
                        else "Architect request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Architect service timeout",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Architect service unavailable",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forward request to Architect: {str(e)}",
        )


async def _forward_to_architect_public(
    method: str,
    path: str,
    settings: Settings,
    query: Optional[dict] = None,
) -> tuple[int, Optional[dict]]:
    """
    Forward public request to Architect (no authentication required).

    Used for Library endpoints which are public data.

    Args:
        method: HTTP method (GET)
        path: Architect API path (e.g., /api/library/categories)
        settings: Application settings
        query: Optional query parameters

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If Architect request fails
    """
    architect_url = settings.ARCHITECT_URL
    url = f"{architect_url}{path}"

    headers = {
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=query,
            )

            # Forward status code and body
            response_data = None
            if response.text:
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"detail": response.text}

            # If not successful, raise HTTPException with Architect's error
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=(
                        response_data.get("detail", "Architect request failed")
                        if response_data
                        else "Architect request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Architect service timeout",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Architect service unavailable",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forward request to Architect: {str(e)}",
        )


# === STRATEGY ROUTES ===


@router.post("/strategies", status_code=201)
async def create_strategy(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Create a new strategy."""
    body = await request.json()
    status_code, data = await _forward_to_architect(
        "POST", "/api/strategies", user_id, settings, body
    )
    return data


@router.get("/strategies")
async def list_strategies(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """List user strategies."""
    query = dict(request.query_params)
    status_code, data = await _forward_to_architect(
        "GET", "/api/strategies", user_id, settings, query=query
    )
    return data


@router.get("/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Get strategy by ID."""
    status_code, data = await _forward_to_architect(
        "GET", f"/api/strategies/{strategy_id}", user_id, settings
    )
    return data


@router.patch("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: UUID,
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Update strategy."""
    body = await request.json()
    status_code, data = await _forward_to_architect(
        "PATCH", f"/api/strategies/{strategy_id}", user_id, settings, body
    )
    return data


@router.delete("/strategies/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Delete strategy."""
    status_code, data = await _forward_to_architect(
        "DELETE", f"/api/strategies/{strategy_id}", user_id, settings
    )
    return Response(status_code=204)


@router.post("/strategies/{strategy_id}/activate")
async def activate_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Activate strategy."""
    status_code, data = await _forward_to_architect(
        "POST", f"/api/strategies/{strategy_id}/activate", user_id, settings
    )
    return data


@router.post("/strategies/{strategy_id}/pause")
async def pause_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Pause strategy."""
    status_code, data = await _forward_to_architect(
        "POST", f"/api/strategies/{strategy_id}/pause", user_id, settings
    )
    return data


@router.post("/strategies/{strategy_id}/archive")
async def archive_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Archive strategy."""
    status_code, data = await _forward_to_architect(
        "POST", f"/api/strategies/{strategy_id}/archive", user_id, settings
    )
    return data


# === CONVERSATION ROUTES ===


@router.post("/conversations", status_code=201)
async def create_conversation(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Create a new conversation."""
    body = await request.json()
    status_code, data = await _forward_to_architect(
        "POST", "/api/conversations", user_id, settings, body
    )
    return data


@router.get("/conversations")
async def list_conversations(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    List conversations with optional filters.
    Supports query parameters like strategy_id, limit, offset.
    """
    query = dict(request.query_params)
    status_code, data = await _forward_to_architect(
        "GET", "/api/conversations", user_id, settings, query=query
    )
    return data


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Get conversation by ID."""
    status_code, data = await _forward_to_architect(
        "GET", f"/api/conversations/{conversation_id}", user_id, settings
    )
    return data


# === ANALYTICS ===


@router.get("/analytics/me")
async def get_user_analytics(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Get current user analytics."""
    status_code, data = await _forward_to_architect(
        "GET", "/api/strategies/analytics/me", user_id, settings
    )
    return data


# === LIBRARY ROUTES (PUBLIC - NO AUTH REQUIRED) ===


@router.get("/library/categories")
async def get_library_categories(
    settings: Settings = Depends(get_settings),
):
    """Get available library categories (public endpoint)."""
    status_code, data = await _forward_to_architect_public(
        "GET", "/api/library/categories", settings
    )
    return data


@router.get("/library/strategies")
async def list_library_strategies(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    """List library strategies with optional filters (public endpoint)."""
    query = dict(request.query_params)
    status_code, data = await _forward_to_architect_public(
        "GET", "/api/library/strategies", settings, query=query
    )
    return data


@router.get("/library/strategies/search")
async def search_library_strategies(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    """Search library strategies (public endpoint)."""
    query = dict(request.query_params)
    status_code, data = await _forward_to_architect_public(
        "GET", "/api/library/strategies/search", settings, query=query
    )
    return data


@router.get("/library/strategies/{strategy_id}")
async def get_library_strategy(
    strategy_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """Get library strategy details (public endpoint)."""
    status_code, data = await _forward_to_architect_public(
        "GET", f"/api/library/strategies/{strategy_id}", settings
    )
    return data


# === COMPILE ROUTE (PUBLIC - NO AUTH REQUIRED) ===


@router.post("/strategies/compile")
async def compile_strategy(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    """Compile strategy JSON to Python code (public endpoint for transparency)."""
    body = await request.json()
    
    architect_url = settings.ARCHITECT_URL
    url = f"{architect_url}/api/strategies/compile"
    
    headers = {"Content-Type": "application/json"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=url,
                headers=headers,
                json=body,
            )
            
            # Always return the response (even if compilation fails)
            # Frontend needs to see compile errors
            response_data = response.json() if response.text else {}
            
            return response_data
            
    except httpx.TimeoutException:
        return {
            "compiles": False,
            "compile_error": "Compilation timeout"
        }
    except httpx.ConnectError:
        return {
            "compiles": False,
            "compile_error": "Architect service unavailable"
        }
    except Exception as e:
        return {
            "compiles": False,
            "compile_error": f"Compilation error: {str(e)}"
        }
