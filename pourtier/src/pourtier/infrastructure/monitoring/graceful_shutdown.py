"""
Graceful Shutdown handler for Pourtier.

Ensures clean shutdown of all resources and pending requests.
"""

import asyncio
import signal
from typing import Callable, List

from pourtier.di.container import get_container
from shared.reporter import SystemReporter


class PourtierGracefulShutdown:
    """
    Graceful shutdown handler.

    Handles:
    - SIGTERM/SIGINT signals
    - Database connection cleanup
    - Redis connection cleanup
    - HTTP session cleanup (Passeur, Courier)
    - Pending request completion (with timeout)
    """

    def __init__(
        self,
        shutdown_timeout: float = 30.0,
        log_dir: str = None,
    ):
        """
        Initialize graceful shutdown handler.

        Args:
            shutdown_timeout: Max seconds to wait for cleanup (default: 30s)
            log_dir: Directory for logs (None for stdout)
        """
        self.shutdown_timeout = shutdown_timeout
        self.reporter = SystemReporter(
            component_name="pourtier",
            log_dir=log_dir,
        )
        self.container = get_container()
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
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown()),
            )

        self.reporter.info(
            "Signal handlers registered for graceful shutdown",
            context="Startup",
        )

    async def shutdown(self) -> None:
        """
        Execute graceful shutdown sequence.

        Order:
        1. Set shutdown event (stops accepting new requests)
        2. Wait for pending requests (with timeout)
        3. Run custom cleanup tasks
        4. Shutdown DI container (closes all connections)
        """
        if self.shutdown_event.is_set():
            return  # Already shutting down

        self.reporter.info(
            "Graceful shutdown initiated",
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
                    timeout=self.shutdown_timeout / 2,
                )

            # 2. Shutdown DI container (closes DB, Redis, HTTP sessions)
            self.reporter.info(
                "Shutting down DI container",
                context="Shutdown",
            )

            await asyncio.wait_for(
                self.container.shutdown(),
                timeout=self.shutdown_timeout / 2,
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
                exc_info=True,
            )

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self.shutdown_event.is_set()
