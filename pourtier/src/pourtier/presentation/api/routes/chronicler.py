"""
Chronicler Proxy Routes.

Forwards market data requests to Chronicler service.
Frontend → Pourtier → Chronicler
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from pourtier.config.settings import Settings, get_settings

router = APIRouter(prefix="/chronicler", tags=["chronicler"])


async def _forward_to_chronicler(
    method: str,
    path: str,
    settings: Settings,
    query: Optional[dict] = None,
    timeout: float = 30.0,
) -> tuple[int, Optional[dict]]:
    """
    Forward request to Chronicler service.

    Args:
        method: HTTP method (GET)
        path: Chronicler API path (e.g., /tokens)
        settings: Application settings
        query: Optional query parameters
        timeout: Request timeout (default 30s)

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If Chronicler request fails
    """
    chronicler_url = settings.CHRONICLER_URL
    url = f"{chronicler_url}{path}"

    headers = {
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
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

            # If not successful, raise HTTPException
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=(
                        response_data.get("detail", "Chronicler request failed")
                        if response_data
                        else "Chronicler request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Chronicler service timeout",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chronicler service unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forward request to Chronicler: {str(e)}",
        )


@router.get("/tokens")
async def get_tokens(
    settings: Settings = Depends(get_settings),
):
    """
    Get list of available tokens.

    Public endpoint - no authentication required.
    Returns all tokens that can be traded on the platform.

    Response:
        Array of tokens with address, symbol, name, decimals, logo_uri
    """
    status_code, data = await _forward_to_chronicler(
        "GET",
        "/tokens",
        settings,
        timeout=10.0,
    )
    return data


@router.get("/health")
async def chronicler_health(
    settings: Settings = Depends(get_settings),
):
    """Check Chronicler service health."""
    status_code, data = await _forward_to_chronicler(
        "GET",
        "/health",
        settings,
        timeout=10.0,
    )
    return data
