"""
Error and warning level emoji definitions.

Covers all error severity levels, retry logic, and debugging.

Usage:
    >>> from shared.reporter.emojis.errors import ErrorEmoji
    >>> print(f"{ErrorEmoji.CRITICAL} Database connection lost")
    🔴 Database connection lost
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class ErrorEmoji(ComponentEmoji):
    """
    Error levels and warning indicators.

    Categories:
        - Severity: Critical, error, warning, debug
        - Recovery: Retry, fallback, timeout
        - Debugging: Debug info, trace
    """

    # ============================================================
    # Severity Levels
    # ============================================================

    CRITICAL = "🔴"  # Critical error (system failure)
    ERROR = "❌"  # Error (operation failed)
    WARNING = "⚠️"  # Warning (potential issue)
    INFO = "ℹ️"  # Information
    DEBUG = "🐛"  # Debug information

    # ============================================================
    # Recovery Operations
    # ============================================================

    RETRY = "🔄"  # Retry attempt
    RETRY_SUCCESS = "✅"  # Retry successful
    RETRY_FAILED = "❌"  # Retry failed
    FALLBACK = "↩️"  # Fallback triggered
    TIMEOUT = "⏱️"  # Operation timeout

    # ============================================================
    # Validation
    # ============================================================

    VALIDATION_ERROR = "🚫"  # Validation failed
    INVALID_INPUT = "❓"  # Invalid input data
    MISSING_DATA = "📭"  # Missing required data
    CONSTRAINT = "⛔"  # Constraint violation

    # ============================================================
    # Exceptions
    # ============================================================

    EXCEPTION = "💥"  # Exception thrown
    ASSERTION = "‼️"  # Assertion failed
    NOT_FOUND = "🔍"  # Resource not found
    FORBIDDEN = "🚫"  # Access forbidden

    # ============================================================
    # Debugging
    # ============================================================

    TRACE = "🔬"  # Stack trace
    BREAKPOINT = "🔴"  # Breakpoint hit
    INSPECT = "🔍"  # Variable inspection
    PROFILING = "⏱️"  # Performance profiling
