"""
Graceful shutdown handler for Passeur.

Coordinates cleanup on SIGTERM/SIGINT:
1. Stop accepting new requests
2. Close Redis connections
3. Stop bridge server
4. Flush event buffers
"""

import asyncio
import signal
from typing import Callable, List

from shared.lifecycle import GracefulShutdown as SharedGracefulShutdown


class PasseurGracefulShutdown:
    """
    Passeur-specific graceful shutdown coordinator.
    
    Wraps shared GracefulShutdown with Passeur-specific cleanup logic.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize graceful shutdown handler.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        self.shared_shutdown = SharedGracefulShutdown(timeout=timeout)
        self._cleanup_handlers: List[Callable] = []

    def register_cleanup(self, handler: Callable) -> None:
        """
        Register cleanup handler.

        Args:
            handler: Async cleanup function
        """
        self._cleanup_handlers.append(handler)
        self.shared_shutdown.on_shutdown(handler)

    def wait_for_signal(self) -> None:
        """
        Block until shutdown signal received.
        
        This is the main blocking call that keeps the service running.
        """
        self.shared_shutdown.wait_for_signal()

    async def shutdown(self) -> None:
        """
        Execute shutdown sequence.
        
        Called automatically on SIGTERM/SIGINT.
        """
        await self.shared_shutdown.shutdown()
