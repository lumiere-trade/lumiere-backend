"""
Courier - WebSocket Event Bus

Orchestrates Clean Architecture components to provide
real-time event broadcasting with optional JWT authentication.
"""

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from shared.health import HealthServer
from shared.observability import MetricsServer
from shared.reporter import SystemReporter

from courier.config.settings import Settings, load_config
from courier.di import Container
from courier.infrastructure.monitoring import (
    CourierGracefulShutdown,
    CourierHealthChecker,
)
from courier.presentation.api.dependencies import set_container
from courier.presentation.api.routes import (
    health_router,
    publish_router,
    websocket_router,
)


class CourierApp:
    """
    Courier application orchestrator.

    Thin coordination layer that initializes and connects
    all Clean Architecture components.

    Responsibilities:
        - Initialize DI container
        - Setup FastAPI application
        - Register API routes
        - Manage application lifecycle with graceful shutdown
        - Start monitoring servers (Health, Metrics)
        - Run uvicorn server
    """

    def __init__(self, settings: Settings):
        """
        Initialize Courier application.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize reporter FIRST
        self.reporter = self._create_reporter()

        # Initialize container with reporter
        self.container = Container(settings, reporter=self.reporter)

        # Create FastAPI app
        self.app = self._create_app()

        # Set global container for FastAPI dependencies
        set_container(self.container)

        # Monitoring servers
        self.metrics_server: Optional[MetricsServer] = None
        self.health_server: Optional[HealthServer] = None

        # Server instance (set during start)
        self.server = None

        self.reporter.info(
            "Courier initialized",
            context="Courier",
            verbose_level=1,
        )

    def _create_reporter(self) -> SystemReporter:
        """
        Create SystemReporter instance.

        Returns:
            Configured SystemReporter
        """
        log_dir = None

        if self.settings.log_file:
            log_dir = os.path.dirname(self.settings.log_file)
            if not log_dir:
                log_dir = "logs"

        return SystemReporter(
            name="courier",
            log_dir=log_dir,
            verbose=1,
            courier_client=None,
        )

    def _create_app(self) -> FastAPI:
        """
        Create FastAPI application with lifespan management.

        Returns:
            Configured FastAPI application
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan context manager with graceful shutdown."""
            # Startup
            await self._on_startup()

            yield

            # Shutdown
            await self._on_shutdown()

        app = FastAPI(
            title="Courier",
            description="WebSocket event broadcasting hub",
            version="1.0.0",
            lifespan=lifespan,
        )

        # Register routes from presentation layer
        app.include_router(websocket_router)
        app.include_router(publish_router)
        app.include_router(health_router)

        return app

    async def _on_startup(self):
        """
        Application startup event handler.

        Initializes shutdown manager, registers signal handlers,
        starts background tasks, and starts monitoring servers.
        """
        self.reporter.info(
            "Courier starting...",
            context="Courier",
            verbose_level=1,
        )

        # Setup graceful shutdown
        shutdown_manager = self.container.shutdown_manager
        shutdown_manager.setup_signal_handlers()
        shutdown_manager.register_cleanup_task(self._graceful_shutdown_callback)

        self.reporter.info(
            f"Graceful shutdown enabled (timeout: {self.settings.shutdown_timeout}s)",
            context="Courier",
            verbose_level=1,
        )

        # Start Metrics Server (port 9090)
        if self.settings.METRICS_ENABLED:
            self.metrics_server = MetricsServer(
                host=self.settings.METRICS_HOST,
                port=self.settings.METRICS_PORT,
            )
            metrics_thread = threading.Thread(
                target=self.metrics_server.start,
                daemon=True,
                name="MetricsServer",
            )
            metrics_thread.start()
            self.reporter.info(
                f"Metrics server started on "
                f"http://{self.settings.METRICS_HOST}:{self.settings.METRICS_PORT}/metrics",
                context="Courier",
                verbose_level=1,
            )

        # Start Health Server (port 9091)
        if self.settings.HEALTH_CHECK_ENABLED:
            health_checker = CourierHealthChecker(
                settings=self.settings,
                connection_manager=self.container.connection_manager,
            )
            self.health_server = HealthServer(
                host=self.settings.HEALTH_HOST,
                port=self.settings.HEALTH_PORT,
                health_checker=health_checker,
            )
            health_thread = threading.Thread(
                target=self.health_server.start,
                daemon=True,
                name="HealthServer",
            )
            health_thread.start()
            self.reporter.info(
                f"Health server started on "
                f"http://{self.settings.HEALTH_HOST}:{self.settings.HEALTH_PORT}/health",
                context="Courier",
                verbose_level=1,
            )

        self.reporter.info(
            f"Host: {self.settings.host}:{self.settings.port}",
            context="Courier",
            verbose_level=1,
        )

        # Log authentication status
        if self.settings.require_auth:
            self.reporter.info(
                "Authentication: ENABLED",
                context="Courier",
                verbose_level=1,
            )
        else:
            self.reporter.info(
                "Authentication: DISABLED",
                context="Courier",
                verbose_level=1,
            )

        # Log configured channels
        channel_count = len(self.settings.channels)
        self.reporter.info(
            f"Channels configured: {channel_count}",
            context="Courier",
            verbose_level=1,
        )

        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _graceful_shutdown_callback(self):
        """
        Callback executed when shutdown is initiated.

        Logs shutdown initiation and starts graceful shutdown sequence.
        """
        self.reporter.warning(
            "Graceful shutdown initiated",
            context="Courier",
            verbose_level=1,
        )

        # Notify all WebSocket clients
        await self._notify_clients_shutdown()

        # Stop the uvicorn server
        if self.server:
            self.server.should_exit = True

    async def _on_shutdown(self):
        """
        Application shutdown event handler.

        Cleanly shuts down all connections, background tasks, and monitoring servers.
        """
        self.reporter.info(
            "Courier shutting down...",
            context="Courier",
            verbose_level=1,
        )

        # Cancel background tasks
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections gracefully
        await self._close_all_connections_gracefully()

        # Shutdown monitoring servers
        if self.metrics_server:
            self.metrics_server.shutdown()
            self.reporter.info("Metrics server shut down", context="Courier")

        if self.health_server:
            self.health_server.shutdown()
            self.reporter.info("Health server shut down", context="Courier")

        self.reporter.info(
            "Courier stopped",
            context="Courier",
            verbose_level=1,
        )

    async def _notify_clients_shutdown(self):
        """
        Notify all connected clients about impending shutdown.

        Sends shutdown notification message to all WebSocket clients.
        """
        conn_manager = self.container.connection_manager
        total = conn_manager.get_total_connections()

        if total == 0:
            return

        self.reporter.info(
            f"Notifying {total} clients of shutdown",
            context="Courier",
            verbose_level=1,
        )

        # Send shutdown notification to all clients
        shutdown_msg = {
            "type": "shutdown",
            "message": "Server is shutting down",
            "code": 1001,
        }

        for channel, subscribers in conn_manager.channels.items():
            for ws in list(subscribers):
                try:
                    await ws.send_json(shutdown_msg)
                except Exception:
                    pass

    async def _close_all_connections_gracefully(self):
        """
        Close all active WebSocket connections gracefully.

        Waits for grace period before forcing close.
        """
        conn_manager = self.container.connection_manager
        grace_period = self.settings.shutdown_grace_period

        # Wait grace period for clients to disconnect
        self.reporter.info(
            f"Waiting {grace_period}s for graceful close",
            context="Courier",
            verbose_level=1,
        )

        await asyncio.sleep(grace_period)

        # Force close remaining connections
        total_closed = 0
        for channel, subscribers in conn_manager.channels.items():
            for ws in list(subscribers):
                try:
                    await ws.close(code=1001, reason="Server shutdown")
                    total_closed += 1
                except Exception:
                    pass

            subscribers.clear()

        if total_closed > 0:
            self.reporter.info(
                f"Closed {total_closed} connections",
                context="Courier",
                verbose_level=1,
            )

    async def _heartbeat_loop(self):
        """
        Periodic heartbeat loop to detect dead connections.

        Sends ping messages to all connected clients at configured interval.
        Automatically removes dead connections.
        Stops when shutdown initiated.
        """
        interval = self.settings.heartbeat_interval
        shutdown_manager = self.container.shutdown_manager

        self.reporter.info(
            f"Heartbeat started (interval: {interval}s)",
            context="Courier",
            verbose_level=1,
        )

        while True:
            # Stop heartbeat if shutting down
            if shutdown_manager.is_shutting_down():
                self.reporter.info(
                    "Heartbeat stopped (shutdown)",
                    context="Courier",
                    verbose_level=1,
                )
                break

            await asyncio.sleep(interval)

            conn_manager = self.container.connection_manager
            total = conn_manager.get_total_connections()

            if total == 0:
                continue

            self.reporter.debug(
                f"Heartbeat -> {total} clients",
                context="Courier",
                verbose_level=3,
            )

            # Send ping to all connections
            for channel, subscribers in conn_manager.channels.items():
                dead_clients = []

                for ws in subscribers:
                    try:
                        await ws.send_json({"type": "ping"})
                    except Exception:
                        dead_clients.append(ws)

                # Cleanup dead connections
                for ws in dead_clients:
                    conn_manager.remove_client(ws, channel)

    async def serve(self):
        """
        Run server with proper signal handling.

        Uses uvicorn.Server API for proper shutdown control.
        """
        config = uvicorn.Config(
            self.app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level,
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()

    def start(self):
        """
        Start Courier server.

        Runs uvicorn server with configured host and port.
        Blocks until server is stopped.
        """
        asyncio.run(self.serve())


def main():
    """
    Main entry point for Courier application.

    Loads configuration and starts the server.
    """
    import sys

    # Load configuration
    config = load_config()

    # Allow port override from command line
    if len(sys.argv) > 1:
        try:
            config.port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    # Create and start application
    app = CourierApp(config)

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nCourier stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
