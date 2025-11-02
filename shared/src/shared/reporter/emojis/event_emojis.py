"""
Event bus and event handling emoji definitions.

Covers event publishing, subscription, and handler execution.

Usage:
    >>> from shared.reporter.emojis.events import EventEmoji
    >>> print(f"{EventEmoji.PUBLISH} Event published")
    📢 Event published
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class EventEmoji(ComponentEmoji):
    """
    Event bus and event handling operations.

    Categories:
        - Publishing: Publish, broadcast
        - Subscription: Subscribe, unsubscribe
        - Handling: Handler execution
        - Queue: Queue operations
    """

    # ============================================================
    # Publishing
    # ============================================================

    PUBLISH = "📢"  # Event published
    BROADCAST = "📡"  # Event broadcast
    EMIT = "✨"  # Event emitted

    # ============================================================
    # Subscription
    # ============================================================

    SUBSCRIBE = "📡"  # Subscription created
    UNSUBSCRIBE = "📭"  # Subscription removed
    SUBSCRIBED = "✅"  # Successfully subscribed

    # ============================================================
    # Event Handling
    # ============================================================

    HANDLER = "🎯"  # Event handler
    PROCESSING = "⚙️"  # Processing event
    HANDLED = "✅"  # Event handled successfully
    HANDLER_ERROR = "❌"  # Handler error

    # ============================================================
    # Queue Operations
    # ============================================================

    QUEUE = "📬"  # Event queued
    DEQUEUE = "📭"  # Event dequeued
    QUEUE_FULL = "🚫"  # Queue full
    QUEUE_EMPTY = "📭"  # Queue empty

    # ============================================================
    # Priority
    # ============================================================

    PRIORITY_HIGH = "🔴"  # High priority event
    PRIORITY_NORMAL = "🟡"  # Normal priority
    PRIORITY_LOW = "🟢"  # Low priority
    PRIORITY_CRITICAL = "🚨"  # Critical priority
