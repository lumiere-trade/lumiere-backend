"""
Use case for broadcasting messages to channels.
"""

from typing import Any, Dict, List

from fastapi import WebSocket

from courier.domain.value_objects import ChannelName, Message


class BroadcastMessageUseCase:
    """
    Use case for broadcasting messages to channel subscribers.

    Handles message validation and delivery to all connected clients.
    """

    async def execute(
        self,
        channel_name: str,
        message_data: Dict[str, Any],
        subscribers: List[WebSocket],
    ) -> int:
        """
        Broadcast message to all channel subscribers.

        Args:
            channel_name: Target channel name
            message_data: Message payload
            subscribers: List of WebSocket connections

        Returns:
            Number of clients that received the message

        Raises:
            ValueError: If channel name or message data is invalid
        """
        # Validate channel name
        channel = ChannelName(channel_name)

        # Validate and create message
        message = Message(message_data)

        # Broadcast to all subscribers
        sent_count = 0
        dead_clients = []

        for ws in subscribers:
            try:
                await ws.send_json(message.data)
                sent_count += 1
            except Exception:
                # Track dead connections for cleanup
                dead_clients.append(ws)

        return sent_count
