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


def _create_log_context(
    connection_id: str,
    channel: str,
    user_id: Optional[str] = None,
    client_id: Optional[str] = None,
    message_type: Optional[str] = None,
) -> dict:
    """
    Create structured logging context.

    Args:
        connection_id: Unique connection identifier
        channel: Channel name
        user_id: Optional user ID
        client_id: Optional client ID
        message_type: Optional message type

    Returns:
        Dictionary with logging context
    """
    context = {
        "connection_id": connection_id,
        "channel": channel,
    }
    if user_id:
        context["user_id"] = user_id
    if client_id:
        context["client_id"] = client_id
    if message_type:
        context["message_type"] = message_type
    return context


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
        f"{Emoji.NETWORK.CONNECTED} WebSocket connection attempt",
        context="WebSocket",
        **_create_log_context(connection_id, channel, user_id),
        verbose_level=2,
    )

    # Check if shutting down BEFORE accepting connection
    shutdown_manager = container.shutdown_manager
    if shutdown_manager.is_shutting_down():
        reporter.warning(
            f"{Emoji.NETWORK.DISCONNECT} Connection rejected: server shutting down",
            context="WebSocket",
            **_create_log_context(connection_id, channel, user_id),
            verbose_level=1,
        )
        await websocket.close(
            code=status.WS_1001_GOING_AWAY,
            reason="Server is shutting down",
        )
        return

    # Accept connection (auth already verified by dependency)
    await websocket.accept()

    reporter.debug(
        f"{Emoji.SUCCESS} WebSocket connection accepted",
        context="WebSocket",
        **_create_log_context(connection_id, channel, user_id),
        verbose_level=3,
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
            f"{Emoji.NETWORK.CONNECTED} Client connected successfully",
            context="WebSocket",
            **_create_log_context(connection_id, channel, user_id, client.client_id),
            total_connections=total_connections,
            wallet_address=wallet_address,
            verbose_level=1,
        )

    except ConnectionLimitExceeded as e:
        # Connection limit exceeded - send error and close
        reporter.warning(
            f"{Emoji.NETWORK.DISCONNECT} Connection rejected: {e.limit_type} limit exceeded",
            context="WebSocket",
            **_create_log_context(connection_id, channel, user_id),
            limit_type=e.limit_type,
            error=str(e),
            verbose_level=1,
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
    rate_limit_identifier = user_id or client.client_id

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
                    f"{Emoji.SYSTEM.SHUTDOWN} Notifying client of shutdown",
                    context="WebSocket",
                    **_create_log_context(
                        connection_id, channel, user_id, client.client_id
                    ),
                    verbose_level=2,
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
                    reporter.debug(
                        "Legacy ping/pong handled",
                        context="WebSocket",
                        **_create_log_context(
                            connection_id, channel, user_id, client.client_id
                        ),
                        verbose_level=3,
                    )
                    continue

                # Validate message
                validation_result = validate_msg_uc.validate_message(data)

                if not validation_result.valid:
                    validation_failures += 1

                    # Log validation failure
                    reporter.warning(
                        f"{Emoji.ERROR} Message validation failed",
                        context="WebSocket",
                        **_create_log_context(
                            connection_id, channel, user_id, client.client_id
                        ),
                        errors=validation_result.errors,
                        message_size=len(data),
                        verbose_level=2,
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
                            f"{Emoji.ERROR} Rate limit exceeded",
                            context="WebSocket",
                            **_create_log_context(
                                connection_id,
                                channel,
                                user_id,
                                client.client_id,
                                message_type,
                            ),
                            retry_after_seconds=retry_after,
                            verbose_level=2,
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

                # Log message processing (only at debug level to avoid log spam)
                reporter.debug(
                    "Message processed successfully",
                    context="WebSocket",
                    **_create_log_context(
                        connection_id, channel, user_id, client.client_id, message_type
                    ),
                    processing_time_ms=round(processing_time_ms, 2),
                    message_size=validation_result.size_bytes,
                    verbose_level=3,
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
                        client.client_id,
                        reporter,
                    )
                else:
                    # Non-control message - could be echoed or processed
                    # For now, just acknowledge receipt
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
                    f"{Emoji.SYSTEM.HEARTBEAT} Heartbeat ping sent",
                    context="WebSocket",
                    **_create_log_context(
                        connection_id, channel, user_id, client.client_id
                    ),
                    verbose_level=3,
                )

    except WebSocketDisconnect:
        # Client disconnected normally
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECT} Client disconnected",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client.client_id if client else None
            ),
            reason="client_disconnect",
            verbose_level=2,
        )

    except Exception as e:
        # Unexpected error during connection
        reporter.error(
            f"{Emoji.ERROR} WebSocket connection error",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client.client_id if client else None
            ),
            error=str(e),
            error_type=type(e).__name__,
            verbose_level=1,
        )

    finally:
        # Calculate connection duration
        connection_duration = time.time() - connection_start_time

        # Log connection summary
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECT} Connection closed",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client.client_id if client else None
            ),
            duration_seconds=round(connection_duration, 2),
            messages_processed=messages_processed,
            validation_failures=validation_failures,
            rate_limit_hits=rate_limit_hits,
            verbose_level=1,
        )

        # Cleanup - remove client from channel
        if client:
            conn_manager.remove_client(websocket, channel)

            # Cleanup empty ephemeral channels
            if manage_uc.should_cleanup_channel(channel):
                if channel in conn_manager.channels:
                    reporter.debug(
                        "Ephemeral channel cleaned up",
                        context="WebSocket",
                        **_create_log_context(
                            connection_id, channel, user_id, client.client_id
                        ),
                        verbose_level=3,
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
            "Invalid JSON in control message",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client_id, message_type
            ),
            verbose_level=2,
        )
        return

    reporter.debug(
        f"Control message: {message_type}",
        context="WebSocket",
        **_create_log_context(connection_id, channel, user_id, client_id, message_type),
        verbose_level=3,
    )

    if message_type == "ping":
        await websocket.send_json({"type": "pong"})

    elif message_type == "subscribe":
        # Future: Handle channel subscription
        target_channel = message.get("channel")
        await websocket.send_json({"type": "subscribed", "channel": target_channel})
        reporter.info(
            f"{Emoji.NETWORK.CONNECTED} Channel subscription requested",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client_id, message_type
            ),
            target_channel=target_channel,
            verbose_level=2,
        )

    elif message_type == "unsubscribe":
        # Future: Handle channel unsubscription
        target_channel = message.get("channel")
        await websocket.send_json({"type": "unsubscribed", "channel": target_channel})
        reporter.info(
            f"{Emoji.NETWORK.DISCONNECT} Channel unsubscription requested",
            context="WebSocket",
            **_create_log_context(
                connection_id, channel, user_id, client_id, message_type
            ),
            target_channel=target_channel,
            verbose_level=2,
        )
