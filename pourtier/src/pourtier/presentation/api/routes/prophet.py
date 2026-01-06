"""
Prophet AI routes - SSE streaming proxy.

Forwards Prophet chat requests with JWT authentication.
Frontend → Pourtier (JWT validation) → Prophet (X-User-ID header)
"""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from pourtier.config.settings import Settings, get_settings
from pourtier.presentation.api.middleware.auth import get_current_user_id

router = APIRouter(prefix="/prophet", tags=["prophet"])


async def _stream_from_prophet(
    method: str,
    path: str,
    user_id: UUID,
    settings: Settings,
    request: Request,
    body: Dict[str, Any] = None,
) -> StreamingResponse:
    """
    Stream SSE from Prophet with authentication.
    
    Args:
        method: HTTP method
        path: Prophet endpoint path
        user_id: Current user ID from JWT
        settings: Application settings
        request: FastAPI request object
        body: Optional request body
        
    Returns:
        StreamingResponse with SSE events
    """
    import httpx
    
    prophet_url = f"{settings.PROPHET_URL}{path}"
    
    headers = {
        "X-User-ID": str(user_id),
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    async def event_generator():
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                method,
                prophet_url,
                headers=headers,
                json=body,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield {
                        "event": "error",
                        "data": f"Prophet error: {response.status_code} - {error_text.decode()}"
                    }
                    return
                
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk.decode()
    
    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat_stream(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Stream chat with Prophet AI.
    
    Accepts chat request and streams SSE events back.
    
    Request Body:
        {
            "message": "Create a strategy...",
            "conversation_id": "optional-uuid",
            "history": [...],
            "strategy_context": {...}
        }
    
    Response: SSE stream with events:
        - metadata: conversation_id
        - token: streaming text tokens
        - progress: strategy generation progress
        - strategy_generated: complete strategy
        - done: completion signal
        - error: error messages
    """
    body = await request.json()
    
    return await _stream_from_prophet(
        "POST",
        "/chat",
        user_id,
        settings,
        request,
        body=body,
    )


@router.get("/health")
async def get_prophet_health(
    user_id: UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Get Prophet service health status.
    
    Response:
        {
            "status": "healthy",
            "service": "prophet",
            "version": "1.0.0",
            ...
        }
    """
    import httpx
    
    prophet_url = f"{settings.PROPHET_URL}/health"
    
    headers = {
        "X-User-ID": str(user_id),
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(prophet_url, headers=headers)
        
        if response.status_code != 200:
            return {
                "status": "unhealthy",
                "error": f"Prophet returned {response.status_code}",
            }
        
        return response.json()
