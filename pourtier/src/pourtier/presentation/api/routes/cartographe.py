"""
Cartographe Proxy Routes.

Forwards backtest requests to Cartographe with X-User-ID header.
Frontend → Pourtier (JWT validation) → Cartographe (X-User-ID)
"""

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

router = APIRouter(prefix="/cartographe", tags=["cartographe"])


async def _forward_to_cartographe(
    method: str,
    path: str,
    user_id: UUID,
    settings: Settings,
    body: Optional[dict] = None,
    query: Optional[dict] = None,
    timeout: float = 60.0,
) -> tuple[int, Optional[dict]]:
    """
    Forward request to Cartographe with X-User-ID header.

    Args:
        method: HTTP method (GET, POST)
        path: Cartographe API path (e.g., /api/cartographe/backtest)
        user_id: Current user ID from JWT token
        settings: Application settings
        body: Optional request body (JSON)
        query: Optional query parameters
        timeout: Request timeout (default 60s for long backtests)

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If Cartographe request fails
    """
    cartographe_url = settings.CARTOGRAPHE_URL
    url = f"{cartographe_url}{path}"

    headers = {
        "X-User-ID": str(user_id),
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
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

            # If not successful, raise HTTPException with Cartographe's error
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=(
                        response_data.get("detail", "Cartographe request failed")
                        if response_data
                        else "Cartographe request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Cartographe service timeout - backtest may be taking longer than expected",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cartographe service unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forward request to Cartographe: {str(e)}",
        )


@router.post("/backtest")
async def run_backtest(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Run backtest on TSDL strategy.

    Forwards request to Cartographe backtesting engine.
    Timeout is 60 seconds to allow for long backtests.

    Request body:
        {
            "tsdl_document": "BEGIN_STRATEGY...",
            "symbol": "SOL/USDT",
            "days_back": 30,
            "initial_capital": 10000.0,
            "timeframe": "1h",
            "slippage": 0.001,
            "commission": 0.001,
            "cache_results": true
        }

    Response:
        {
            "backtest_id": "uuid",
            "metrics": {...},
            "equity_curve": [...],
            "trades": [...],
            "market_data": [...]
        }
    """
    body = await request.json()
    status_code, data = await _forward_to_cartographe(
        "POST",
        "/api/cartographe/backtest",
        user_id,
        settings,
        body,
        timeout=60.0,
    )
    return data


@router.get("/health")
async def cartographe_health(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """Check Cartographe service health."""
    status_code, data = await _forward_to_cartographe(
        "GET",
        "/health",
        user_id,
        settings,
        timeout=10.0,
    )
    return data
