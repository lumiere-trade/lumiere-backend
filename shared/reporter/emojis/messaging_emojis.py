"""
Messaging platforms and notifications emoji definitions.

Covers Telegram, Slack, commands, and user interactions.

Usage:
    >>> from shared.reporter.emojis.messaging import MessageEmoji
    >>> print(f"{MessageEmoji.TELEGRAM} Message sent")
    📱 Message sent
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class MessageEmoji(ComponentEmoji):
    """
    Messaging platforms and user notifications.

    Categories:
        - Platforms: Telegram, Slack, Email
        - Message Types: Notification, command, response
        - UI: Menus, buttons, interactions
    """

    # ============================================================
    # Platforms
    # ============================================================

    TELEGRAM = "📱"  # Telegram operation
    SLACK = "💬"  # Slack message
    EMAIL = "📧"  # Email notification
    SMS = "📲"  # SMS message

    # ============================================================
    # Message Types
    # ============================================================

    NOTIFICATION = "🔔"  # General notification
    ALERT = "🚨"  # Alert/urgent notification
    INFO = "ℹ️"  # Information message
    WARNING = "⚠️"  # Warning message
    SUCCESS = "✅"  # Success notification

    # ============================================================
    # Commands & Interactions
    # ============================================================

    COMMAND = "⚡"  # Command received
    RESPONSE = "💬"  # Response sent
    CALLBACK = "🔙"  # Callback query
    ACTION = "🎬"  # Action performed

    # ============================================================
    # UI Elements
    # ============================================================

    MENU = "📋"  # Menu display
    BUTTON = "🔘"  # Button interaction
    KEYBOARD = "⌨️"  # Inline keyboard
    LINK = "🔗"  # Link/URL

    # ============================================================
    # Queue & Delivery
    # ============================================================

    QUEUED = "📬"  # Message queued
    SENT = "📤"  # Message sent
    DELIVERED = "✅"  # Message delivered
    FAILED = "❌"  # Delivery failed
    RATE_LIMIT = "🚫"  # Rate limit hit
