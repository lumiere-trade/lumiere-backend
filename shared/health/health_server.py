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

from .checks import HealthChecker

logger = logging.getLogger(__name__)


class HealthRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoints."""

    health_checker: Optional[HealthChecker] = None

    def log_message(self, format, *args):
        """Override to use logging instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")

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
            logger.error(f"Liveness check failed: {e}")
            self._send_error_response(500, str(e))

    def _handle_readiness(self):
        """Handle /health/ready endpoint."""
        try:
            report = self.health_checker.check_readiness()
            status_code = 200 if report.is_ready else 503
            self._send_json_response(status_code, report.to_dict())
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
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
            status_code, {"error": "Internal Server Error", "message": message}
        )


class HealthServer:
    """
    HTTP server for health check endpoints.

    Example:
        class MyHealthChecker:
            def check_liveness(self) -> HealthReport:
                return HealthReport(...)

            def check_readiness(self) -> HealthReport:
                return HealthReport(...)

        checker = MyHealthChecker()
        server = HealthServer(checker, port=8080)
        server.start()
    """

    def __init__(
        self,
        health_checker: HealthChecker,
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        """
        Initialize health server.

        Args:
            health_checker: Health checker implementation
            host: Host to bind to
            port: Port to listen on
        """
        self.health_checker = health_checker
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None

        HealthRequestHandler.health_checker = health_checker

    def start(self):
        """Start the health check server."""
        try:
            self.server = HTTPServer((self.host, self.port), HealthRequestHandler)
            logger.info(f"Health server listening on {self.host}:{self.port}")

            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

            self.server.serve_forever()

        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            raise

    def stop(self):
        """Stop the health check server."""
        if self.server:
            logger.info("Stopping health server...")
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health server stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
