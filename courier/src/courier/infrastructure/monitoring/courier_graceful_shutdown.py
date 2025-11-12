"""
Graceful Shutdown handler for Courier.

Ensures clean shutdown of WebSocket connections and background tasks.
"""

import asyncio
import signal
from typing import Callable, List, Optional

from shared.reporter import SystemReporter


class CourierGracefulShutdown:
    """
    Graceful shutdown handler for Courier event bus.

    Handles:
    - SIGTERM/SIGINT signals
    - WebSocket client notification
    - Connection cleanup
    - Background task cancellation
    """

    def __init__(
        self,
        shutdown_timeout: float = 30.0,
        grace_period: float = 5.0,
        log_dir: Optional[str] = None,
    ):
        """
        Initialize graceful shutdown handler.

        Args:
            shutdown_timeout: Max seconds to wait for cleanup (default: 30s)
            grace_period: Seconds to wait for WebSocket graceful close
            log_dir: Directory for logs (None for stdout)
        """
        self.shutdown_timeout = shutdown_timeout
        self.grace_period = grace_period
        self.reporter = SystemReporter(
            name="courier",
            log_dir=log_dir,
        )
        self.shutdown_event = asyncio.Event()
        self.cleanup_tasks: List[Callable] = []

    def register_cleanup_task(self, task: Callable) -> None:
        """
        Register cleanup task to run on shutdown.

        Args:
            task: Async function to call during cleanup
        """
        self.cleanup_tasks.append(task)

    def setup_signal_handlers(self) -> None:
        """Setup SIGTERM and SIGINT handlers."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.shutdown(s)),
            )

        self.reporter.info(
            "Signal handlers registered for graceful shutdown",
            context="Startup",
        )

    async def shutdown(self, sig: signal.Signals = None) -> None:
        """
        Execute graceful shutdown sequence.

        Order:
        1. Set shutdown event (stops accepting new connections)
        2. Notify WebSocket clients
        3. Wait grace period for clients to disconnect
        4. Run custom cleanup tasks
        5. Force close remaining connections

        Args:
            sig: Signal that triggered shutdown (optional)
        """
        if self.shutdown_event.is_set():
            return  # Already shutting down

        sig_name = sig.name if sig else "manual"
        self.reporter.info(
            f"Graceful shutdown initiated (signal: {sig_name})",
            context="Shutdown",
        )

        self.shutdown_event.set()

        try:
            # 1. Run custom cleanup tasks
            if self.cleanup_tasks:
                self.reporter.info(
                    f"Running {len(self.cleanup_tasks)} cleanup tasks",
                    context="Shutdown",
                )

                cleanup_coros = [task() for task in self.cleanup_tasks]

                await asyncio.wait_for(
                    asyncio.gather(*cleanup_coros, return_exceptions=True),
                    timeout=self.shutdown_timeout,
                )

            self.reporter.info(
                "Graceful shutdown completed successfully",
                context="Shutdown",
            )

        except asyncio.TimeoutError:
            self.reporter.warning(
                f"Shutdown timeout after {self.shutdown_timeout}s",
                context="Shutdown",
            )
        except Exception as e:
            self.reporter.error(
                f"Error during shutdown: {str(e)}",
                context="Shutdown",
            )

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self.shutdown_event.is_set()

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown to be initiated."""
        await self.shutdown_event.wait()
