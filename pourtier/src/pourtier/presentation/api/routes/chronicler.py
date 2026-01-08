"""
Chronicler Proxy Routes.

Forwards market data requests to Chronicler service.
Frontend -> Pourtier -> Chronicler
"""

from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

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


# === OHLCV ROUTES ===


@router.get("/ohlcv")
async def get_ohlcv_candles(
    token_address: str = Query(..., description="Token mint address"),
    timeframe: str = Query(..., description="Candle timeframe (1m, 5m, 1h, etc)"),
    start_time: datetime = Query(..., description="Start time (ISO format)"),
    end_time: datetime = Query(..., description="End time (ISO format)"),
    settings: Settings = Depends(get_settings),
):
    """
    Get OHLCV candles for a token.

    Public endpoint - no authentication required.
    Used by frontend to load historical chart data.

    Query Parameters:
        token_address: Solana token mint address
        timeframe: Candle timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        start_time: Start datetime (ISO format)
        end_time: End datetime (ISO format)

    Response:
        {
            "candles": [
                {
                    "token_address": "So11...",
                    "timestamp": "2026-01-08T12:00:00Z",
                    "timeframe": "1h",
                    "open": "190.50",
                    "high": "191.20",
                    "low": "189.80",
                    "close": "190.90",
                    "volume": "1234567.89",
                    "trades_count": 1234
                }
            ],
            "count": 200,
            "token_address": "So11...",
            "timeframe": "1h",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-08T12:00:00Z"
        }
    """
    query_params = {
        "token_address": token_address,
        "timeframe": timeframe,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }

    status_code, data = await _forward_to_chronicler(
        "GET",
        "/ohlcv",
        settings,
        query=query_params,
        timeout=60.0,  # Longer timeout for large data requests
    )
    return data


@router.get("/ohlcv/latest")
async def get_latest_candle(
    token_address: str = Query(..., description="Token mint address"),
    timeframe: str = Query(..., description="Candle timeframe"),
    settings: Settings = Depends(get_settings),
):
    """
    Get latest candle for a token.

    Public endpoint - no authentication required.
    Used for real-time price display.

    Query Parameters:
        token_address: Solana token mint address
        timeframe: Candle timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)

    Response:
        {
            "token_address": "So11...",
            "timestamp": "2026-01-08T12:00:00Z",
            "timeframe": "1h",
            "open": "190.50",
            "high": "191.20",
            "low": "189.80",
            "close": "190.90",
            "volume": "1234567.89",
            "trades_count": 1234
        }
    """
    query_params = {
        "token_address": token_address,
        "timeframe": timeframe,
    }

    status_code, data = await _forward_to_chronicler(
        "GET",
        "/ohlcv/latest",
        settings,
        query=query_params,
        timeout=10.0,
    )
    return data


# === TOKEN ROUTES ===


@router.get("/tokens")
async def get_tokens(
    settings: Settings = Depends(get_settings),
):
    """
    Get list of available tokens.

    Public endpoint - no authentication required.
    Returns all tokens that can be traded on the platform.

    Response:
        [
            {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "decimals": 9,
                "logo_uri": "https://..."
            }
        ]
    """
    status_code, data = await _forward_to_chronicler(
        "GET",
        "/tokens",
        settings,
        timeout=10.0,
    )
    return data


@router.get("/tokens/{token_address}/metrics")
async def get_token_metrics(
    token_address: str,
    settings: Settings = Depends(get_settings),
):
    """
    Get token metrics (liquidity, volume, etc).

    Public endpoint - no authentication required.
    Returns current metrics with warning if low liquidity/volume.

    Response:
        {
            "token_address": "So11...",
            "liquidity_usd": "1234567.89",
            "volume_24h_usd": "9876543.21",
            "last_update": "2026-01-08T12:00:00Z",
            "warning": null
        }
    """
    status_code, data = await _forward_to_chronicler(
        "GET",
        f"/tokens/{token_address}/metrics",
        settings,
        timeout=10.0,
    )
    return data


# === HEALTH ROUTE ===


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
