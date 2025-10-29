"""
WebSocket endpoint with Clean Architecture.
"""

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from courier.di import Container
from courier.presentation.api.dependencies import (
    authenticate_websocket,
    get_container,
)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    auth_payload=Depends(authenticate_websocket),
    container: Container = Depends(get_container),
):
    """
    WebSocket endpoint for real-time event streaming.

    Supports optional JWT authentication via query parameter.
    Rejects new connections during graceful shutdown.

    Args:
        websocket: WebSocket connection
        channel: Channel name to subscribe to
        auth_payload: Authentication payload (from dependency)
        container: DI container (from dependency)

    Connection examples:
        - ws://localhost:8765/ws/global
        - ws://localhost:8765/ws/user.123?token=eyJ...
    """
    # Check if shutting down BEFORE accepting connection
    shutdown_manager = container.shutdown_manager
    if shutdown_manager.is_shutting_down():
        await websocket.close(
            code=status.WS_1001_GOING_AWAY,
            reason="Server is shutting down",
        )
        return

    # Accept connection (auth already verified by dependency)
    await websocket.accept()

    # Get managers and use cases
    conn_manager = container.connection_manager
    manage_uc = container.get_manage_channel_use_case()

    # Create or get channel
    manage_uc.create_or_get_channel(channel)

    # Extract user info from auth payload
    user_id = auth_payload.user_id if auth_payload else None
    wallet_address = auth_payload.wallet_address if auth_payload else None

    # Add client to channel
    client = conn_manager.add_client(
        websocket,
        channel,
        user_id=user_id,
        wallet_address=wallet_address,
    )

    # Update statistics
    container.increment_stat("total_connections")

    # Log connection (use shared reporter if available)
    auth_info = f"user_id={user_id}" if user_id else "unauthenticated"

    try:
        # Keep connection alive and handle messages
        while True:
            # Check shutdown state during connection
            if shutdown_manager.is_shutting_down():
                await websocket.send_json({
                    "type": "shutdown",
                    "message": "Server is shutting down",
                })
                await websocket.close(
                    code=status.WS_1001_GOING_AWAY,
                    reason="Server shutdown",
                )
                break

            try:
                # Wait for message with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Increment message counter
                container.increment_stat("total_messages_received")

                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send heartbeat ping
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    finally:
        # Cleanup - remove client from channel
        conn_manager.remove_client(websocket, channel)

        # Cleanup empty ephemeral channels
        if manage_uc.should_cleanup_channel(channel):
            if channel in conn_manager.channels:
                del conn_manager.channels[channel]
