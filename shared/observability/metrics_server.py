"""
Generic Prometheus metrics HTTP server.

Exposes /metrics endpoint for Prometheus scraping.
Uses wsgiref.simple_server (stdlib) for lightweight HTTP serving.

Can be used by any microservice to expose Prometheus metrics.
"""

import logging
import signal
from typing import Optional
from wsgiref.simple_server import WSGIServer, make_server

from prometheus_client import make_wsgi_app


class MetricsServer:
    """
    Standalone HTTP server for Prometheus metrics.

    Serves /metrics endpoint on configurable host and port.
    Supports graceful shutdown via SIGTERM/SIGINT.

    Example:
        from shared.observability import MetricsServer

        # Define your metrics
        from prometheus_client import Counter
        requests_total = Counter('requests_total', 'Total requests')

        # Start server
        server = MetricsServer(host="0.0.0.0", port=9090)
        server.start()  # Blocks until SIGTERM/SIGINT
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9090) -> None:
        """
        Initialize metrics server.

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 9090)
        """
        self.host = host
        self.port = port
        self.httpd: Optional[WSGIServer] = None
        self.logger = logging.getLogger(__name__)
        self._running = False

    def start(self) -> None:
        """
        Start the metrics server.

        Blocks until shutdown signal received or KeyboardInterrupt.

        Raises:
            OSError: If port is already in use
        """
        # Create WSGI app from prometheus_client
        app = make_wsgi_app()

        # Create HTTP server
        try:
            self.httpd = make_server(self.host, self.port, app)
            self._running = True
        except OSError as e:
            self.logger.error(f"Failed to bind to {self.host}:{self.port}: {e}")
            raise

        # Setup signal handlers for graceful shutdown (only in main thread)
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signal handlers only work in main thread
            pass

        # Log startup
        self.logger.info(
            f"Metrics server started on http://{self.host}:{self.port}/metrics"
        )

        # Serve forever (until signal received)
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            self.shutdown()

    def start_in_background(self) -> None:
        """
        Start the metrics server in a background thread.

        Returns immediately, allowing main thread to continue.

        Example:
            server = MetricsServer(port=9090)
            server.start_in_background()
            # Continue with main application logic
        """
        import threading

        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        self.logger.info(
            f"Metrics server started in background on "
            f"http://{self.host}:{self.port}/metrics"
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        if self.httpd and self._running:
            self.logger.info("Shutting down metrics server")
            self._running = False
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def url(self) -> str:
        """Get the full URL of the metrics endpoint."""
        return f"http://{self.host}:{self.port}/metrics"


def run_metrics_server(port: int = 9090, host: str = "0.0.0.0") -> None:
    """
    Run standalone Prometheus metrics server.

    Convenience function to start metrics server with default settings.
    Blocks until SIGTERM/SIGINT received.

    Args:
        port: Port to bind to (default: 9090)
        host: Host to bind to (default: 0.0.0.0)

    Example:
        >>> from shared.observability import run_metrics_server
        >>> run_metrics_server(port=9090)
    """
    server = MetricsServer(host=host, port=port)
    server.start()


__all__ = ["MetricsServer", "run_metrics_server"]
