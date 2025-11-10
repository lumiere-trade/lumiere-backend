"""
WebSocket endpoint with Clean Architecture and production logging.
"""

import asyncio
import json
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji

from courier.di import Container
from courier.infrastructure.websocket import ConnectionLimitExceeded
from courier.presentation.api.dependencies import (
    authenticate_websocket,
    get_container,
)

router = APIRouter(tags=["websocket"])


def _generate_connection_id() -> str:
    """Generate unique connection ID for tracking."""
    return f"conn_{uuid.uuid4().hex[:12]}"


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
    Validates all incoming messages.
    Enforces per-message-type rate limiting.
    Enforces connection limits (global, per-user, per-channel).

    Args:
        websocket: WebSocket connection
        channel: Channel name to subscribe to
        auth_payload: Authentication payload (from dependency)
        container: DI container (from dependency)

    Connection examples:
        - ws://localhost:8765/ws/global
        - ws://localhost:8765/ws/user.123?token=eyJ...
    """
    # Generate unique connection ID for tracking
    connection_id = _generate_connection_id()

    # Get reporter for logging
    reporter = container.reporter

    # Extract user info from auth payload
    user_id = auth_payload.user_id if auth_payload else None
    wallet_address = auth_payload.wallet_address if auth_payload else None

    # Log connection attempt
    reporter.info(
        f"{Emoji.NETWORK.CONNECTED} WebSocket connection attempt "
        f"[conn={connection_id}] [channel={channel}] [user={user_id}]",
        context="WebSocket",
    )

    # Check if shutting down BEFORE accepting connection
    shutdown_manager = container.shutdown_manager
    if shutdown_manager.is_shutting_down():
        reporter.warning(
            f"{Emoji.NETWORK.DISCONNECTED} Connection rejected: server shutting down "
            f"[conn={connection_id}] [channel={channel}]",
            context="WebSocket",
        )
        await websocket.close(
            code=status.WS_1001_GOING_AWAY,
            reason="Server is shutting down",
        )
        return

    # Accept connection (auth already verified by dependency)
    await websocket.accept()

    reporter.debug(
        f"{Emoji.SUCCESS} WebSocket connection accepted "
        f"[conn={connection_id}] [channel={channel}]",
        context="WebSocket",
    )

    # Get managers and use cases
    conn_manager = container.connection_manager
    manage_uc = container.get_manage_channel_use_case()
    validate_msg_uc = container.get_validate_message_use_case()
    rate_limiter = container.websocket_rate_limiter

    # Create or get channel
    manage_uc.create_or_get_channel(channel)

    # Add client to channel with connection limit check
    client = None
    try:
        client = conn_manager.add_client(
            websocket,
            channel,
            user_id=user_id,
            wallet_address=wallet_address,
        )

        # Log successful connection
        total_connections = conn_manager.get_total_connections()
        reporter.info(
            f"{Emoji.NETWORK.CONNECTED} Client connected successfully "
            f"[conn={connection_id}] [channel={channel}] [client={client.id}] "
            f"[total_connections={total_connections}]",
            context="WebSocket",
        )

    except ConnectionLimitExceeded as e:
        # Connection limit exceeded - send error and close
        reporter.warning(
            f"{Emoji.NETWORK.DISCONNECTED} Connection rejected: {e.limit_type} limit exceeded "
            f"[conn={connection_id}] [channel={channel}]",
            context="WebSocket",
        )

        error_response = {
            "type": "error",
            "code": "CONNECTION_LIMIT_EXCEEDED",
            "message": str(e),
            "limit_type": e.limit_type,
        }
        await websocket.send_json(error_response)
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Connection limit exceeded",
        )

        # Track rejection
        container.increment_connection_rejection(e.limit_type)
        return

    # Update statistics
    container.increment_stat("total_connections")

    # Use user_id for rate limiting, fallback to client_id
    rate_limit_identifier = user_id or client.id

    # Track connection start time for duration logging
    connection_start_time = time.time()
    messages_processed = 0
    validation_failures = 0
    rate_limit_hits = 0

    try:
        # Keep connection alive and handle messages
        while True:
            # Check shutdown state during connection
            if shutdown_manager.is_shutting_down():
                reporter.info(
                    f"{Emoji.SYSTEM.SHUTDOWN} Notifying client of shutdown [conn={connection_id}]",
                    context="WebSocket",
                )

                await websocket.send_json(
                    {
                        "type": "shutdown",
                        "message": "Server is shutting down",
                    }
                )
                await websocket.close(
                    code=status.WS_1001_GOING_AWAY,
                    reason="Server shutdown",
                )
                break

            try:
                # Wait for message with timeout
                message_start_time = time.time()
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Increment message counter
                container.increment_stat("total_messages_received")
                messages_processed += 1

                # Handle legacy ping/pong (simple text)
                if data == "ping":
                    await websocket.send_text("pong")
                    reporter.debug("Legacy ping/pong handled", context="WebSocket")
                    continue

                # Validate message
                validation_result = validate_msg_uc.validate_message(data)

                if not validation_result.valid:
                    validation_failures += 1

                    # Log validation failure
                    reporter.warning(
                        f"{Emoji.ERROR} Message validation failed [conn={connection_id}] "
                        f"[errors={validation_result.errors}]",
                        context="WebSocket",
                    )

                    # Send validation error to client
                    error_response = {
                        "type": "error",
                        "code": "VALIDATION_ERROR",
                        "message": "Message validation failed",
                        "errors": validation_result.errors,
                    }
                    await websocket.send_json(error_response)

                    # Track validation failure
                    container.increment_stat("validation_failures")
                    continue

                # Extract message type for rate limiting
                message_type = validation_result.message_type

                # Check per-message-type rate limit
                if rate_limiter:
                    is_allowed = await rate_limiter.check_rate_limit(
                        rate_limit_identifier,
                        message_type=message_type,
                    )

                    if not is_allowed:
                        rate_limit_hits += 1

                        # Rate limit exceeded
                        retry_after = rate_limiter.get_retry_after_seconds(
                            rate_limit_identifier,
                            message_type=message_type,
                        )

                        # Log rate limit hit
                        reporter.warning(
                            f"{Emoji.ERROR} Rate limit exceeded [conn={connection_id}] "
                            f"[message_type={message_type}] [retry_after={retry_after}s]",
                            context="WebSocket",
                        )

                        error_response = {
                            "type": "error",
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded for message type '{message_type}'",
                            "retry_after_seconds": retry_after,
                            "message_type": message_type,
                        }
                        await websocket.send_json(error_response)

                        # Track rate limit hit
                        container.increment_rate_limit_hit(message_type)
                        continue

                # Calculate message processing latency
                processing_time_ms = (time.time() - message_start_time) * 1000

                # Log message processing (only at debug level)
                reporter.debug(
                    f"Message processed [conn={connection_id}] [type={message_type}] "
                    f"[time={processing_time_ms:.2f}ms] [size={validation_result.size_bytes}]",
                    context="WebSocket",
                )

                # Message is valid and within rate limit - handle control messages
                if validate_msg_uc.is_control_message(message_type):
                    # Handle control messages (ping, subscribe, etc.)
                    await _handle_control_message(
                        websocket,
                        message_type,
                        data,
                        connection_id,
                        channel,
                        user_id,
                        client.id,
                        reporter,
                    )
                else:
                    # Non-control message - acknowledge receipt
                    ack_response = {
                        "type": "ack",
                        "message_type": message_type,
                        "size_bytes": validation_result.size_bytes,
                    }
                    await websocket.send_json(ack_response)

            except asyncio.TimeoutError:
                # Send heartbeat ping
                await websocket.send_json({"type": "ping"})
                reporter.debug(
                    f"{Emoji.SYSTEM.HEARTBEAT} Heartbeat ping sent", context="WebSocket"
                )

    except WebSocketDisconnect:
        # Client disconnected normally
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECTED} Client disconnected [conn={connection_id}] "
            f"[channel={channel}]",
            context="WebSocket",
        )

    except Exception as e:
        # Unexpected error during connection
        reporter.error(
            f"{Emoji.ERROR} WebSocket connection error [conn={connection_id}]: {type(e).__name__}: {str(e)}",
            context="WebSocket",
        )

    finally:
        # Calculate connection duration
        connection_duration = time.time() - connection_start_time

        # Log connection summary
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECTED} Connection closed [conn={connection_id}] "
            f"[duration={connection_duration:.2f}s] [messages={messages_processed}] "
            f"[validation_failures={validation_failures}] [rate_limit_hits={rate_limit_hits}]",
            context="WebSocket",
        )

        # Cleanup - remove client from channel
        if client:
            conn_manager.remove_client(websocket, channel)

            # Cleanup empty ephemeral channels
            if manage_uc.should_cleanup_channel(channel):
                if channel in conn_manager.channels:
                    reporter.debug(
                        f"Ephemeral channel cleaned up [channel={channel}]",
                        context="WebSocket",
                    )
                    del conn_manager.channels[channel]


async def _handle_control_message(
    websocket: WebSocket,
    message_type: str,
    raw_data: str,
    connection_id: str,
    channel: str,
    user_id: Optional[str],
    client_id: Optional[str],
    reporter: SystemReporter,
) -> None:
    """
    Handle control messages (ping, subscribe, etc.).

    Args:
        websocket: WebSocket connection
        message_type: Type of control message
        raw_data: Raw message data
        connection_id: Unique connection identifier
        channel: Channel name
        user_id: Optional user ID
        client_id: Optional client ID
        reporter: SystemReporter for logging
    """
    try:
        message = json.loads(raw_data)
    except json.JSONDecodeError:
        reporter.warning(
            f"Invalid JSON in control message [conn={connection_id}]",
            context="WebSocket",
        )
        return

    reporter.debug(
        f"Control message: {message_type} [conn={connection_id}]", context="WebSocket"
    )

    if message_type == "ping":
        await websocket.send_json({"type": "pong"})

    elif message_type == "subscribe":
        # Future: Handle channel subscription
        target_channel = message.get("channel")
        await websocket.send_json({"type": "subscribed", "channel": target_channel})
        reporter.info(
            f"{Emoji.NETWORK.CONNECTED} Channel subscription requested "
            f"[conn={connection_id}] [target={target_channel}]",
            context="WebSocket",
        )

    elif message_type == "unsubscribe":
        # Future: Handle channel unsubscription
        target_channel = message.get("channel")
        await websocket.send_json({"type": "unsubscribed", "channel": target_channel})
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECTED} Channel unsubscription requested "
            f"[conn={connection_id}] [target={target_channel}]",
            context="WebSocket",
        )
