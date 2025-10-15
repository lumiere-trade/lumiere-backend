"""
Network operations and communication emoji definitions.

Covers WebSocket, REST API, connections, and data streaming.

Usage:
    >>> from shared.reporter.emojis.network import NetworkEmoji
    >>> print(f"{NetworkEmoji.CONNECTED} WebSocket connected")
    🔗 WebSocket connected
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class NetworkEmoji(ComponentEmoji):
    """
    Network operations and communication.

    Categories:
        - Connection: Connect, disconnect, reconnect
        - Data Flow: Send, receive, broadcast
        - Protocols: WebSocket, HTTP, RPC
        - Feeds: Price feeds, streams
    """

    # ============================================================
    # Connection States
    # ============================================================

    CONNECTED = "🔗"  # Connection established
    DISCONNECTED = "⚠️"  # Connection lost
    RECONNECTING = "🔄"  # Reconnection attempt
    CONNECTING = "⏳"  # Connection in progress
    TIMEOUT = "⏱️"  # Connection timeout

    # ============================================================
    # Data Flow
    # ============================================================

    SEND = "📤"  # Data sent
    RECEIVE = "📥"  # Data received
    BROADCAST = "📡"  # Broadcasting to clients
    UPLOAD = "⬆️"  # Upload operation
    DOWNLOAD = "⬇️"  # Download operation

    # ============================================================
    # Protocol Types
    # ============================================================

    WEBSOCKET = "🌐"  # WebSocket operation
    HTTP = "🔌"  # HTTP/REST API
    RPC = "⚡"  # RPC call (Solana)
    GRAPHQL = "🔷"  # GraphQL query

    # ============================================================
    # Feed Operations
    # ============================================================

    FEED = "📊"  # Price feed update
    STREAM = "🌊"  # Live data stream
    SUBSCRIPTION = "📬"  # Stream subscription
    UNSUBSCRIBE = "📭"  # Stream unsubscription

    # ============================================================
    # Performance
    # ============================================================

    FAST = "⚡"  # Fast response
    SLOW = "🐌"  # Slow response
    LATENCY = "⏱️"  # Latency measurement
    BANDWIDTH = "📶"  # Bandwidth usage
