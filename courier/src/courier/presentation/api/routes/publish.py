"""
Event publishing endpoints with Clean Architecture, Schema Validation and Rate Limiting.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import ValidationError

from courier.di import Container
from courier.presentation.api.dependencies import get_container
from courier.presentation.schemas import PublishRequest, PublishResponse

router = APIRouter(tags=["publish"])


@router.post("/publish", response_model=PublishResponse)
async def publish_event(
    publish_request: PublishRequest,
    request: Request,
    container: Container = Depends(get_container),
    x_service_name: Optional[str] = Header(None, alias="X-Service-Name"),
):
    """
    Publish event to channel with schema validation and rate limiting.

    Recommended endpoint for new implementations.

    Args:
        publish_request: Publish request with channel and data
        request: FastAPI request (for setting headers via background)
        container: DI container
        x_service_name: Optional service name header for validation

    Returns:
        Publication result with clients reached

    Raises:
        HTTPException: 
            - 400: Invalid channel name or event validation fails
            - 429: Rate limit exceeded
    """
    # Rate limiting check (if enabled)
    rate_limiter = container.publish_rate_limiter
    if rate_limiter and x_service_name:
        is_allowed = await rate_limiter.check_rate_limit(x_service_name)
        
        if not is_allowed:
            # Get rate limit info
            stats = rate_limiter.get_stats(x_service_name)
            retry_after = stats["retry_after_seconds"]
            
            # Increment rate limit hit counter
            container.increment_stat("rate_limit_hits")
            
            # Return 429 with rate limit info
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests from service '{x_service_name}'",
                    "limit": stats["limit"],
                    "window_seconds": stats["window_seconds"],
                    "retry_after_seconds": retry_after,
                    "reset_at": stats["reset_at"].isoformat() if stats["reset_at"] else None,
                },
                headers={
                    "X-RateLimit-Limit": str(stats["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(stats["reset_at"].timestamp()) if stats["reset_at"] else 0
                    ),
                    "Retry-After": str(retry_after),
                },
            )

    # Get use cases
    manage_uc = container.get_manage_channel_use_case()
    broadcast_uc = container.get_broadcast_use_case()
    validate_uc = container.get_validate_event_use_case()

    # Extract event type from data for validation
    event_type = publish_request.data.get("type")
    
    # Validate event schema if event type is provided
    if event_type:
        try:
            # Validate against Pydantic schema
            validated_event = validate_uc.execute(event_type, publish_request.data)
            
            # Check if source matches service name header (if provided)
            if x_service_name:
                event_source = publish_request.data.get("metadata", {}).get("source")
                if event_source and event_source != x_service_name:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "Event source mismatch",
                            "message": (
                                f"Event source '{event_source}' does not match "
                                f"X-Service-Name header '{x_service_name}'"
                            ),
                        },
                    )
            
            # Use validated event data
            message_data = validated_event.model_dump()
            
        except ValueError as e:
            # Unknown event type or validation error
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Event validation failed",
                    "message": str(e),
                    "event_type": event_type,
                },
            )
        except ValidationError as e:
            # Pydantic validation error
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Event schema validation failed",
                    "message": "Event data does not match required schema",
                    "event_type": event_type,
                    "validation_errors": e.errors(),
                },
            )
    else:
        # No event type provided - use data as-is (backwards compatibility)
        message_data = publish_request.data

    # Ensure channel exists (auto-create if needed)
    try:
        manage_uc.create_or_get_channel(publish_request.channel)
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid channel name: {str(e)}"
        )

    # Get channel subscribers
    subscribers = container.connection_manager.get_channel_subscribers(
        publish_request.channel
    )

    # Broadcast message to all subscribers
    try:
        sent_count = await broadcast_uc.execute(
            publish_request.channel,
            message_data,
            subscribers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid message data: {str(e)}"
        )

    # Update statistics
    container.increment_stat("total_messages_sent", sent_count)

    return PublishResponse(
        channel=publish_request.channel,
        clients_reached=sent_count,
    )


@router.post("/publish/{channel}", response_model=PublishResponse)
async def publish_event_legacy(
    channel: str,
    event: dict,
    request: Request,
    container: Container = Depends(get_container),
    x_service_name: Optional[str] = Header(None, alias="X-Service-Name"),
):
    """
    Publish event to channel (channel in URL).

    Legacy endpoint for backwards compatibility.

    Args:
        channel: Target channel name
        event: Event payload
        request: FastAPI request
        container: DI container
        x_service_name: Optional service name header for validation

    Returns:
        Publication result
    """
    # Convert to new request format
    publish_request = PublishRequest(channel=channel, data=event)

    # Use new endpoint logic
    return await publish_event(publish_request, request, container, x_service_name)
