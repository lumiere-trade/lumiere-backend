"""
Chevalier Proxy Routes.

Forwards deployment requests to Chevalier with X-User-ID header.
Frontend -> Pourtier (JWT validation) -> Chevalier (X-User-ID)

Includes WebSocket proxy for real-time dashboard streaming.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chevalier", tags=["chevalier"])


class DeployStrategyRequest(BaseModel):
    """Deploy strategy request payload."""
    strategy_id: UUID = Field(..., description="Architect strategy UUID")
    strategy_json: Dict[str, Any]
    initial_capital: float = Field(..., gt=0)
    is_paper_trading: bool = True


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
        path: Chevalier API path (e.g., /api/chevalier/strategies/deploy)
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


# === WEBSOCKET PROXY ===


@router.websocket("/ws/deployment/{deployment_id}")
async def websocket_proxy(
    websocket: WebSocket,
    deployment_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """
    WebSocket proxy to Chevalier for real-time dashboard streaming.

    Proxies WebSocket connection from frontend to Chevalier.
    No JWT validation for WebSocket (handled by deployment ownership check in Chevalier).

    Message types from Chevalier:
    - connected: Initial connection confirmation
    - candle: New OHLCV candle data
    - indicators: Current indicator values
    - position: Position status update
    - signal: Trade signal generated

    Client can send:
    - ping: Keep-alive ping (server responds with pong)
    """
    import websockets

    # Build Chevalier WebSocket URL
    chevalier_url = settings.CHEVALIER_URL
    # Convert http:// to ws://
    ws_url = chevalier_url.replace("http://", "ws://").replace("https://", "wss://")
    chevalier_ws_url = f"{ws_url}/api/chevalier/ws/deployment/{deployment_id}"

    logger.info(f"WebSocket proxy connecting to: {chevalier_ws_url}")

    # Accept frontend connection
    await websocket.accept()

    try:
        # Connect to Chevalier WebSocket
        async with websockets.connect(chevalier_ws_url) as chevalier_ws:
            logger.info(f"WebSocket proxy connected for deployment {deployment_id}")

            async def forward_to_frontend():
                """Forward messages from Chevalier to frontend."""
                try:
                    async for message in chevalier_ws:
                        await websocket.send_text(message)
                except websockets.ConnectionClosed:
                    logger.info("Chevalier WebSocket closed")
                except Exception as e:
                    logger.error(f"Error forwarding to frontend: {e}")

            async def forward_to_chevalier():
                """Forward messages from frontend to Chevalier."""
                try:
                    while True:
                        data = await websocket.receive_text()
                        await chevalier_ws.send(data)
                except WebSocketDisconnect:
                    logger.info("Frontend WebSocket disconnected")
                except Exception as e:
                    logger.error(f"Error forwarding to Chevalier: {e}")

            # Run both directions concurrently
            await asyncio.gather(
                forward_to_frontend(),
                forward_to_chevalier(),
                return_exceptions=True
            )

    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"Chevalier WebSocket connection closed: {e}")
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass


# === DEPLOYMENT ROUTES ===


@router.post("/strategies/deploy", status_code=status.HTTP_201_CREATED)
async def deploy_strategy(
    request: DeployStrategyRequest,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Deploy strategy for live trading.

    Creates a new deployment instance with versioning.
    Only ONE active deployment per architect_strategy_id allowed.

    Request Body:
        {
            "strategy_id": "uuid (Architect strategy ID)",
            "strategy_json": { ... TSDL strategy JSON ... },
            "initial_capital": 10000.0,
            "is_paper_trading": true
        }

    Response:
        {
            "deployment_id": "uuid",
            "architect_strategy_id": "uuid",
            "version": 1,
            "status": "ACTIVE",
            "created_at": "2026-01-06T18:00:00Z",
            "is_paper_trading": true
        }
    """
    # Construct payload with user_id from JWT and strategy_id from request
    payload = {
        "strategy_id": str(request.strategy_id),
        "user_id": str(user_id),
        "strategy_json": request.strategy_json,
        "initial_capital": request.initial_capital,
        "is_paper_trading": request.is_paper_trading,
    }

    status_code, data = await _forward_to_chevalier(
        "POST",
        "/api/chevalier/strategies/deploy",
        user_id,
        settings,
        body=payload,
        timeout=30.0,
    )
    return data


@router.post("/strategies/deployments/{deployment_id}/pause")
async def pause_deployment(
    deployment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Pause active deployment.

    Stops signal evaluation but keeps subscriptions active.
    Can be resumed later without re-warmup.
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/chevalier/strategies/deployments/{deployment_id}/pause",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


@router.post("/strategies/deployments/{deployment_id}/resume")
async def resume_deployment(
    deployment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Resume paused deployment.

    Restores indicator state and restarts evaluation.
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/chevalier/strategies/deployments/{deployment_id}/resume",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


@router.post("/strategies/deployments/{deployment_id}/stop")
async def stop_deployment(
    deployment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Stop deployment permanently.

    Closes any open positions and marks deployment as stopped.
    Deployment can be undeployed after stopping.
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/chevalier/strategies/deployments/{deployment_id}/stop",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


@router.post("/strategies/deployments/{deployment_id}/undeploy")
async def undeploy_deployment(
    deployment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Undeploy (archive) deployment.

    Final lifecycle action - deployment moves to UNDEPLOYED status.
    Requires deployment to be STOPPED first.
    """
    status_code, data = await _forward_to_chevalier(
        "POST",
        f"/api/chevalier/strategies/deployments/{deployment_id}/undeploy",
        user_id,
        settings,
        timeout=30.0,
    )
    return data


# IMPORTANT: Static routes BEFORE dynamic routes to avoid path conflicts
@router.get("/strategies/deployments/active")
async def get_active_deployments(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get all active deployments for current user.

    Response:
        [
            {
                "deployment_id": "uuid",
                "architect_strategy_id": "uuid",
                "version": 1,
                "status": "ACTIVE",
                "user_id": "uuid",
                "token_symbol": "SOL/USDC",
                "current_capital": 10000.0,
                "is_paper_trading": true,
                "created_at": "2026-01-06T18:00:00Z"
            }
        ]
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        f"/api/chevalier/strategies/deployments/active?user_id={user_id}",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


@router.get("/strategies/deployments/{deployment_id}")
async def get_deployment_status(
    deployment_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get deployment status by deployment instance ID.
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        f"/api/chevalier/strategies/deployments/{deployment_id}",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


# Dynamic routes with path parameters AFTER static routes
@router.get("/strategies/{architect_strategy_id}/active")
async def get_active_deployment(
    architect_strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get active deployment for specific Architect strategy.

    Returns 404 if no active deployment exists.
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        f"/api/chevalier/strategies/{architect_strategy_id}/active",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


@router.get("/strategies/{architect_strategy_id}/history")
async def get_deployment_history(
    architect_strategy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get deployment history for Architect strategy.

    Returns all deployments (active + archived) ordered by version DESC.
    """
    status_code, data = await _forward_to_chevalier(
        "GET",
        f"/api/chevalier/strategies/{architect_strategy_id}/history",
        user_id,
        settings,
        timeout=10.0,
    )
    return data


@router.get("/health")
async def chevalier_health(
    settings: Settings = Depends(get_settings),
):
    """
    Check Chevalier service health (no auth required).
    """
    chevalier_url = settings.CHEVALIER_URL
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{chevalier_url}/health")
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chevalier health check failed: {str(e)}",
        )
