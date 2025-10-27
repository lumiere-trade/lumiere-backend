"""
Event publishing endpoints with Clean Architecture.
"""

from fastapi import APIRouter, Depends, HTTPException

from courier.di import Container
from courier.presentation.api.dependencies import get_container
from courier.presentation.schemas import PublishRequest, PublishResponse

router = APIRouter(tags=["publish"])


@router.post("/publish", response_model=PublishResponse)
async def publish_event(
    request: PublishRequest,
    container: Container = Depends(get_container),
):
    """
    Publish event to channel (channel in body).

    Recommended endpoint for new implementations.

    Args:
        request: Publish request with channel and data
        container: DI container

    Returns:
        Publication result with clients reached

    Raises:
        HTTPException: If channel name is invalid
    """
    # Get use cases
    manage_uc = container.get_manage_channel_use_case()
    broadcast_uc = container.get_broadcast_use_case()

    # Ensure channel exists (auto-create if needed)
    try:
        manage_uc.create_or_get_channel(request.channel)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel name: {str(e)}"
        )

    # Get channel subscribers
    subscribers = container.connection_manager.get_channel_subscribers(
        request.channel
    )

    # Broadcast message to all subscribers
    try:
        sent_count = await broadcast_uc.execute(
            request.channel,
            request.data,
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
        channel=request.channel,
        clients_reached=sent_count,
    )


@router.post("/publish/{channel}", response_model=PublishResponse)
async def publish_event_legacy(
    channel: str,
    event: dict,
    container: Container = Depends(get_container),
):
    """
    Publish event to channel (channel in URL).

    Legacy endpoint for backwards compatibility.

    Args:
        channel: Target channel name
        event: Event payload
        container: DI container

    Returns:
        Publication result
    """
    # Convert to new request format
    request = PublishRequest(channel=channel, data=event)

    # Use new endpoint logic
    return await publish_event(request, container)
