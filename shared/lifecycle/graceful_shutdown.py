"""
Graceful shutdown handler for microservices.

Handles SIGTERM and SIGINT signals to allow clean service termination.
"""
import signal
import asyncio
import logging
from typing import List, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ShutdownConfig:
    """Configuration for graceful shutdown."""

    timeout: float = 30.0
    """Maximum time to wait for shutdown handlers (seconds)"""

    signal_handlers: tuple = (signal.SIGTERM, signal.SIGINT)
    """Signals to handle"""


class GracefulShutdown:
    """
    Manages graceful shutdown of services.

    Example:
        shutdown = GracefulShutdown()

        @shutdown.on_shutdown
        async def cleanup():
            await db.close()
            await redis.close()
            logger.info("Cleanup complete")

        # Start service...
        shutdown.wait_for_signal()
    """

    def __init__(self, config: Optional[ShutdownConfig] = None):
        self.config = config or ShutdownConfig()
        self._shutdown_handlers: List[Callable] = []
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Register signal handlers."""
        for sig in self.config.signal_handlers:
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signal."""
        logger.info(
            f"Received signal {signum}, initiating graceful shutdown..."
        )
        self._shutdown_event.set()

    def on_shutdown(self, func: Callable):
        """
        Register a shutdown handler.

        Args:
            func: Async function to call on shutdown

        Returns:
            The function (allows use as decorator)
        """
        self._shutdown_handlers.append(func)
        return func

    async def shutdown(self):
        """Execute all shutdown handlers."""
        logger.info(
            f"Running {len(self._shutdown_handlers)} shutdown handlers..."
        )

        for handler in self._shutdown_handlers:
            try:
                await asyncio.wait_for(
                    handler(), timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Shutdown handler {handler.__name__} timed out"
                )
            except Exception as e:
                logger.error(
                    f"Error in shutdown handler {handler.__name__}: {e}"
                )

        logger.info("Graceful shutdown complete")

    def wait_for_signal(self):
        """Block until shutdown signal received."""
        asyncio.run(self._wait_and_shutdown())

    async def _wait_and_shutdown(self):
        """Wait for signal and execute shutdown."""
        await self._shutdown_event.wait()
        await self.shutdown()


__all__ = ["GracefulShutdown", "ShutdownConfig"]
