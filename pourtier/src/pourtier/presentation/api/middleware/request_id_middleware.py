"""
Request ID middleware for request tracking.
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from pourtier.infrastructure.monitoring.logger import (
    get_request_id,
    set_request_id,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track request IDs.

    Adds X-Request-ID header to responses.
    No logging - keeps middleware lean and focused.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with ID tracking.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or set_request_id()
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = get_request_id() or ""

        return response
