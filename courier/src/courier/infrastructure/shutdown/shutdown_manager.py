"""
Graceful shutdown manager.

Handles:
- Signal registration (SIGTERM, SIGINT)
- Shutdown state tracking
- WebSocket client notification
- Request completion timeout
- Clean exit coordination
"""

import asyncio
import signal
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional


class ShutdownState(Enum):
    """Shutdown state enum."""

    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class ShutdownManager:
    """
    Manages graceful shutdown of Courier service.

    Coordinates shutdown sequence:
    1. Catch shutdown signals
    2. Set shutdown flag
    3. Notify WebSocket clients
    4. Wait for in-flight requests
    5. Force close after timeout
    6. Exit cleanly

    Attributes:
        state: Current shutdown state
        shutdown_timeout: Max seconds to wait for shutdown
        grace_period: Seconds to wait for WebSocket close
        shutdown_started_at: Timestamp when shutdown initiated
    """

    def __init__(
        self,
        shutdown_timeout: int = 30,
        grace_period: int = 5,
    ):
        """
        Initialize shutdown manager.

        Args:
            shutdown_timeout: Maximum seconds to wait for complete shutdown
            grace_period: Seconds to wait for graceful WebSocket closure
        """
        self.shutdown_timeout = shutdown_timeout
        self.grace_period = grace_period

        self.state = ShutdownState.RUNNING
        self.shutdown_started_at: Optional[datetime] = None
        self._shutdown_event = asyncio.Event()
        self._shutdown_callbacks: List[Callable] = []
        self._original_handlers = {}

    def is_shutting_down(self) -> bool:
        """
        Check if shutdown is in progress.

        Returns:
            True if shutting down, False otherwise
        """
        return self.state in (ShutdownState.SHUTTING_DOWN, ShutdownState.SHUTDOWN)

    def is_running(self) -> bool:
        """
        Check if service is running normally.

        Returns:
            True if running, False if shutting down
        """
        return self.state == ShutdownState.RUNNING

    def register_shutdown_callback(self, callback: Callable) -> None:
        """
        Register callback to be called on shutdown.

        Callbacks are called in registration order.

        Args:
            callback: Async function to call on shutdown
        """
        self._shutdown_callbacks.append(callback)

    def setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.

        Registers handlers for:
        - SIGTERM (Docker/K8s stop)
        - SIGINT (Ctrl+C)

        Preserves original handlers for restoration.
        """
        # Store original handlers
        self._original_handlers = {
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
            signal.SIGINT: signal.getsignal(signal.SIGINT),
        }

        # Register shutdown handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_signal)

    def restore_signal_handlers(self) -> None:
        """
        Restore original signal handlers.

        Called after shutdown complete.
        """
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)

    def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle shutdown signal.

        Sets shutdown flag and triggers shutdown sequence.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        sig_name = signal.Signals(signum).name

        # Trigger shutdown
        asyncio.create_task(self.initiate_shutdown(sig_name))

    async def initiate_shutdown(self, reason: str = "manual") -> None:
        """
        Initiate graceful shutdown sequence.

        Args:
            reason: Reason for shutdown (signal name, manual, etc.)
        """
        if self.state != ShutdownState.RUNNING:
            return  # Already shutting down

        self.state = ShutdownState.SHUTTING_DOWN
        self.shutdown_started_at = datetime.utcnow()

        # Set shutdown event
        self._shutdown_event.set()

        # Execute shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception:
                # Continue shutdown even if callback fails
                pass

    async def wait_for_shutdown(self) -> None:
        """
        Wait for shutdown to be initiated.

        Blocks until shutdown signal received.
        """
        await self._shutdown_event.wait()

    async def wait_for_shutdown_complete(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for shutdown to complete.

        Args:
            timeout: Optional timeout in seconds (uses shutdown_timeout if None)

        Returns:
            True if shutdown completed within timeout, False if timed out
        """
        timeout = timeout or self.shutdown_timeout

        try:
            await asyncio.wait_for(self._shutdown_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def mark_shutdown_complete(self) -> None:
        """
        Mark shutdown as complete.

        Called after all cleanup is done.
        """
        self.state = ShutdownState.SHUTDOWN

    def get_shutdown_info(self) -> dict:
        """
        Get shutdown status information.

        Returns:
            Dictionary with shutdown status details
        """
        return {
            "state": self.state.value,
            "is_shutting_down": self.is_shutting_down(),
            "shutdown_started_at": (
                self.shutdown_started_at.isoformat()
                if self.shutdown_started_at
                else None
            ),
            "shutdown_timeout": self.shutdown_timeout,
            "grace_period": self.grace_period,
        }
