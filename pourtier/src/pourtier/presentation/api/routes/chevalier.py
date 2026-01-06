"""
Chevalier Proxy Routes.

Forwards deployment requests to Chevalier with X-User-ID header.
Frontend → Pourtier (JWT validation) → Chevalier (X-User-ID)
"""

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

router = APIRouter(prefix="/chevalier", tags=["chevalier"])


async def _forward_to_chevalier(
    method: str,
    path: str,
    user_id: UUID,
    settings: Settings,
    body: Optional[dict] = None,
    query: Optional[dict] = None,
    timeout: float = 30.0,
) -> tuple[int, Optional[dict]]:
    """
    Forward request to Chevalier with X-User-ID header.

    Args:
        method: HTTP method (GET, POST)
        path: Chevalier API path (e.g., /api/strategies/{id}/deploy)
        user_id: Current user ID from JWT token
        settings: Application settings
        body: Optional request body (JSON)
        query: Optional query parameters
        timeout: Request timeout (default 30s)

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If Chevalier request fails
    """
    chevalier_url = settings.CHEVALIER_URL
    url = f"{chevalier_url}{path}"

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

            # If not successful, raise HTTPException with Chevalier's error
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=(
                        response_data.get("detail", "Chevalier request failed")
                        if response_data
                        else "Chevalier request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Chevalier service timeout",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chevalier service unavailable",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forward request to Chevalier: {str(e)}",
        )


# === DEPLOYMENT ROUTES ===


@router.post("/strategies/{strategy_id}/deploy")
async def deploy_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Deploy strategy for live trading.

    Request validation:
    - User must own the strategy (verified by Chevalier)
    - Strategy must be in valid state
    - User must have sufficient escrow balance

    Response:
        {
            "execution_id": "uuid",
            "strategy_id": "uuid",
            "status": "STARTING" | "RUNNING",
            "deployed_at": "2025-01-06T15:30:00Z",
            "message": "Strategy deployed successfully"
        }
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/strategies/{strategy_id}/deploy",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


@router.post("/strategies/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Stop running strategy.

    Gracefully stops strategy execution:
    - Closes all open positions (if configured)
    - Stops signal generation
    - Marks execution as STOPPED

    Response:
        {
            "execution_id": "uuid",
            "strategy_id": "uuid",
            "status": "STOPPING" | "STOPPED",
            "stopped_at": "2025-01-06T16:30:00Z",
            "message": "Strategy stopped successfully"
        }
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/strategies/{strategy_id}/stop",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


@router.get("/strategies/{strategy_id}/status")
async def get_execution_status(
    strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get strategy execution status.

    Returns real-time execution metrics:
    - Current status (STARTING, RUNNING, STOPPED, ERROR)
    - Runtime statistics (signals, trades, PnL)
    - Resource usage (CPU, memory)
    - Last activity timestamps

    Response:
        {
            "execution_id": "uuid",
            "strategy_id": "uuid",
            "user_id": "uuid",
            "status": "RUNNING",
            "deployed_at": "2025-01-06T15:30:00Z",
            "stopped_at": null,
            "error_message": null,
            "signals_today": 5,
            "trades_today": 3,
            "pnl_today": 125.50,
            "last_signal_at": "2025-01-06T16:25:00Z",
            "last_trade_at": "2025-01-06T16:20:00Z",
            "cpu_percent": 2.5,
            "memory_mb": 128.0,
            "uptime_seconds": 3600
        }
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        f"/api/strategies/{strategy_id}/status",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


@router.get("/executions/active")
async def get_active_executions(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get all active executions for current user.

    Returns list of running strategies with status.

    Response:
        {
            "executions": [
                {
                    "execution_id": "uuid",
                    "strategy_id": "uuid",
                    "status": "RUNNING",
                    "deployed_at": "2025-01-06T15:30:00Z",
                    "signals_today": 5,
                    "trades_today": 3,
                    "pnl_today": 125.50
                }
            ]
        }
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        "/api/executions/active",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


@router.get("/health")
async def chevalier_health(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Check Chevalier service health.

    Response:
        {
            "status": "healthy",
            "service": "Chevalier",
            "version": "1.0.0",
            "active_executions": 5
        }
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        "/health",
        user_id,
        settings,
        timeout=10.0,
    )
    return data
