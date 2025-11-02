"""
System-level operations and lifecycle emoji definitions.
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class SystemEmoji(ComponentEmoji):
    """System-level operations and lifecycle events."""

    # ============================================================
    # Lifecycle Operations
    # ============================================================
    STARTUP = "🚀"  # System/component initialization
    SHUTDOWN = "🛑"  # System/component shutdown
    READY = "✅"  # Component initialized successfully
    RESTART = "🔄"  # System restart operation
    INIT = "🆕"  # Initialization state

    # ============================================================
    # Configuration
    # ============================================================
    CONFIG = "⚙️"  # Configuration operation
    CONFIG_LOAD = "📋"  # Configuration loading
    CONFIG_VALID = "✔️"  # Configuration validated
    CONFIG_ERROR = "❌"  # Configuration error

    # ============================================================
    # Build & Factory
    # ============================================================
    BUILD = "🏗️"  # Building/constructing components
    REGISTER = "📝"  # Service registration
    UNREGISTER = "📤"  # Service unregistration
    DISCOVER = "🔍"  # Service discovery

    # ============================================================
    # Health & Monitoring
    # ============================================================
    HEARTBEAT = "❤️"  # Heartbeat/health check pulse
    ALIVE = "💚"  # System alive confirmation
    HEALTH_CHECK = "🩺"  # Health check performed
    PING = "🏓"  # Ping operation
    PONG = "🏓"  # Pong response

    # ============================================================
    # Maintenance & Cleanup
    # ============================================================
    CLEANUP = "🧹"  # Resource cleanup
    GARBAGE_COLLECT = "🗑️"  # Garbage collection
    RESET = "♻️"  # Reset to initial state
    UPDATE = "🔄"  # Update operation
