"""
Health check HTTP server.

Provides HTTP endpoints for health checks:
- GET /health - Overall health (readiness)
- GET /health/live - Liveness probe
- GET /health/ready - Readiness probe
"""

import json
import logging
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from .health_checker import HealthChecker


class HealthRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoints."""

    # Class-level health checker (shared across requests)
    health_checker: Optional[HealthChecker] = None

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/health/live":
            self._handle_liveness()
        elif self.path == "/health/ready":
            self._handle_readiness()
        else:
            self._handle_404()

    def _handle_health(self):
        """Handle /health endpoint (same as /health/ready)."""
        self._handle_readiness()

    def _handle_liveness(self):
        """Handle /health/live endpoint."""
        try:
            report = self.health_checker.check_liveness()
            status_code = 200 if report.is_healthy else 503
            self._send_json_response(status_code, report.to_dict())
        except Exception as e:
            self._send_error_response(500, str(e))

    def _handle_readiness(self):
        """Handle /health/ready endpoint."""
        try:
            report = self.health_checker.check_readiness()
            status_code = 200 if report.is_ready else 503
            self._send_json_response(status_code, report.to_dict())
        except Exception as e:
            self._send_error_response(500, str(e))

    def _handle_404(self):
        """Handle 404 Not Found."""
        self._send_json_response(
            404,
            {
                "error": "Not Found",
                "message": f"Path {self.path} not found",
                "available_endpoints": [
                    "/health",
                    "/health/live",
                    "/health/ready",
                ],
            },
        )

    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode("utf-8"))

    def _send_error_response(self, status_code: int, message: str):
        """Send error response."""
        self._send_json_response(
            status_code,
            {
                "error": "Internal Server Error",
                "message": message,
            },
        )

    def log_message(self, format, *args):
        """Override to use Python logging instead of stderr."""
        logger = logging.getLogger(__name__)
        logger.info(f"{self.address_string()} - {format % args}")


class HealthServer:
    """
    Health check HTTP server.

    Serves health check endpoints for monitoring and orchestration.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        health_checker: Optional[HealthChecker] = None,
    ):
        """
        Initialize health server.

        Args:
            host: Host to bind to
            port: Port to bind to
            health_checker: Health checker instance (creates new if None)
        """
        self.host = host
        self.port = port
        self.health_checker = health_checker or HealthChecker()
        self.httpd: Optional[HTTPServer] = None
        self.logger = logging.getLogger(__name__)
        self._running = False

        # Set health checker on handler class
        HealthRequestHandler.health_checker = self.health_checker

    def start(self) -> None:
        """
        Start the health server.

        Blocks until shutdown signal received.

        Raises:
            OSError: If port is already in use
        """
        try:
            self.httpd = HTTPServer((self.host, self.port), HealthRequestHandler)
            self._running = True
        except OSError as e:
            self.logger.error(f"Failed to bind to {self.host}:{self.port}: {e}")
            raise

        # Setup signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signal handlers only work in main thread
            pass

        self.logger.info(f"Health server started on http://{self.host}:{self.port}")
        print(f"Health server running on http://{self.host}:{self.port}")
        print("Endpoints:")
        print(f"  - http://{self.host}:{self.port}/health")
        print(f"  - http://{self.host}:{self.port}/health/live")
        print(f"  - http://{self.host}:{self.port}/health/ready")
        print("Press Ctrl+C to stop")

        # Serve forever
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            self.shutdown()

    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        if self.httpd and self._running:
            print("\nShutting down health server...")
            self.logger.info("Shutting down health server")
            self._running = False
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None


def run_health_server(
    port: int = 8080,
    host: str = "0.0.0.0",
    smoke_test_timeout: Optional[float] = None,
) -> None:
    """
    Run standalone health check server.

    Convenience function to start health server with default settings.

    Args:
        port: Port to bind to
        host: Host to bind to
        smoke_test_timeout: Timeout for smoke test (uses config if None)

    Example:
        >>> from tsdl.infrastructure.health import run_health_server
        >>> run_health_server(port=8080, host="0.0.0.0")
    """
    health_checker = HealthChecker(smoke_test_timeout=smoke_test_timeout)
    server = HealthServer(host=host, port=port, health_checker=health_checker)
    server.start()
