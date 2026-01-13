"""
TSDL Proxy Routes.

Forwards metadata requests to TSDL service.
Frontend → Pourtier (JWT auth) → TSDL
"""

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

router = APIRouter(prefix="/tsdl", tags=["tsdl"])


async def _forward_to_tsdl(
    method: str,
    path: str,
    settings: Settings,
    user_id: Optional[UUID] = None,
    timeout: float = 10.0,
) -> tuple[int, Optional[dict]]:
    """
    Forward request to TSDL service.

    Args:
        method: HTTP method (GET)
        path: TSDL API path (e.g., /metadata/indicators)
        settings: Application settings
        user_id: Optional user ID (for authenticated requests)
        timeout: Request timeout (default 10s)

    Returns:
        Tuple of (status_code, response_json)

    Raises:
        HTTPException: If TSDL request fails
    """
    tsdl_url = settings.TSDL_URL
    url = f"{tsdl_url}{path}"

    headers = {
        "Content-Type": "application/json",
    }

    # Add user ID header if provided (optional for metadata endpoints)
    if user_id:
        headers["X-User-ID"] = str(user_id)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
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
                        response_data.get("detail", "TSDL request failed")
                        if response_data
                        else "TSDL request failed"
                    ),
                )

            return (response.status_code, response_data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="TSDL service timeout",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TSDL service unavailable",
        )
    except HTTPException:
        raise


@router.get("/metadata/indicators")
async def get_indicator_metadata(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get indicator metadata from TSDL service.

    Returns specifications for all available indicators including:
    - Parameters (type, min, max, default)
    - Description
    - Output type
    - Category
    - Examples

    Response:
        {
            "SMA": {
                "description": "Simple Moving Average",
                "parameters": {...},
                "output": "series",
                "category": "trend",
                "examples": ["SMA(20)", "SMA(50)"]
            },
            ...
        }
    """
    status_code, data = await _forward_to_tsdl(
        "GET",
        "/metadata/indicators",
        settings,
        user_id,
    )

    return data


@router.get("/metadata/operators")
async def get_operator_metadata(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get operator metadata from TSDL service.

    Returns specifications for logical operators (AND, OR, etc.)

    Response:
        {
            "AND": {
                "description": "Logical AND",
                "usage": "Combines conditions...",
                "examples": ["0 AND 1"]
            },
            ...
        }
    """
    status_code, data = await _forward_to_tsdl(
        "GET",
        "/metadata/operators",
        settings,
        user_id,
    )

    return data


@router.get("/metadata/parameters")
async def get_parameter_metadata(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get risk parameter metadata from TSDL service.

    Returns specifications for stop_loss, take_profit, trailing_stop:
    - Type, min, max, default, step, unit
    - Required flag
    - Description
    - Examples
    - Validation rules

    Response:
        {
            "stop_loss": {
                "type": "number",
                "min": 0.1,
                "max": 20.0,
                "default": 2.0,
                "step": 0.1,
                "unit": "%",
                "required": true,
                "description": "Maximum loss before auto-exit",
                "examples": [1.5, 2.0, 2.5, 3.0]
            },
            ...
        }
    """
    status_code, data = await _forward_to_tsdl(
        "GET",
        "/metadata/parameters",
        settings,
        user_id,
    )

    return data


@router.post("/data/all")
async def extract_all_data(
    request: dict,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Extract all data from TSDL code.
    
    Proxies request to TSDL service for parsing tsdl_code.
    """
    async def _forward_post_to_tsdl(
        path: str,
        json_body: dict,
    ) -> tuple[int, Optional[dict]]:
        tsdl_url = settings.TSDL_URL
        url = f"{tsdl_url}{path}"
        
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": str(user_id),
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url=url,
                    json=json_body,
                    headers=headers,
                )
                
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.json().get("detail", "TSDL request failed"),
                    )
                
                return (response.status_code, response.json())
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="TSDL service timeout",
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TSDL service unavailable",
            )
    
    status_code, data = await _forward_post_to_tsdl("/data/all", request)
    return data
