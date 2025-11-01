"""
Timeout context manager for operations.

Provides cross-platform timeout support for long-running operations.
Uses signal.alarm() on Unix, threading.Timer on Windows/threads.
"""

import platform
import signal
import threading
from contextlib import contextmanager
from typing import Optional


class TimeoutError(Exception):
    """Raised when operation exceeds timeout."""

    def __init__(self, operation: str, timeout: float):
        """
        Initialize timeout error.

        Args:
            operation: Name of operation that timed out
            timeout: Timeout duration in seconds
        """
        self.operation = operation
        self.timeout = timeout
        super().__init__(
            f"Operation '{operation}' exceeded timeout of {timeout} seconds"
        )


class TimeoutContext:
    """
    Context manager for operation timeouts.

    Uses signal.alarm() on Unix (main thread only).
    Uses threading.Timer on Windows or in threads.
    """

    def __init__(self, timeout: float, operation: str = "operation"):
        """
        Initialize timeout context.

        Args:
            timeout: Timeout in seconds
            operation: Operation name for error messages
        """
        self.timeout = timeout
        self.operation = operation
        self.timer: Optional[threading.Timer] = None
        self.timed_out = False

    def _timeout_handler(self, signum=None, frame=None):
        """Handle timeout signal."""
        self.timed_out = True
        raise TimeoutError(self.operation, self.timeout)

    def _timeout_thread(self):
        """Thread-based timeout handler."""
        self.timed_out = True
        # Note: Can't raise exception from thread, must check flag

    def __enter__(self):
        """Enter timeout context."""
        # Try signal-based timeout first (Unix, main thread only)
        if platform.system() != "Windows":
            try:
                signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(int(self.timeout))
                return self
            except ValueError:
                # Not in main thread, fall back to timer
                pass

        # Fall back to timer-based timeout
        self.timer = threading.Timer(self.timeout, self._timeout_thread)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit timeout context."""
        # Cancel signal alarm
        if platform.system() != "Windows":
            try:
                signal.alarm(0)
            except ValueError:
                pass

        # Cancel timer
        if self.timer:
            self.timer.cancel()

        # Check if we timed out (for timer-based timeout)
        if self.timed_out and exc_type is None:
            raise TimeoutError(self.operation, self.timeout)

        return False


@contextmanager
def timeout(seconds: float, operation: str = "operation"):
    """
    Context manager for operation timeout.

    Args:
        seconds: Timeout duration in seconds
        operation: Operation name for error messages

    Yields:
        None

    Raises:
        TimeoutError: If operation exceeds timeout

    Example:
        >>> with timeout(5.0, "parse"):
        ...     result = long_running_parse()
    """
    ctx = TimeoutContext(seconds, operation)
    with ctx:
        yield
