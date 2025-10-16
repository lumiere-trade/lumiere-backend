"""
Prometheus metrics middleware for FastAPI.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from pourtier.infrastructure.monitoring import metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics.

    Records:
    - Request count by method/endpoint/status
    - Request duration by method/endpoint
    - Error count by method/endpoint/type
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        # Extract endpoint path (without query params)
        endpoint = request.url.path
        method = request.method

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record duration
            duration = time.time() - start_time
            metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            # Record request count
            metrics.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
            ).inc()

            # Record errors (4xx/5xx)
            if response.status_code >= 400:
                error_type = (
                    "client_error" if response.status_code < 500 else "server_error"
                )
                metrics.http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type,
                ).inc()

            return response

        except Exception as e:
            # Record duration even on exception
            duration = time.time() - start_time
            metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            # Record error
            metrics.http_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__,
            ).inc()

            raise
