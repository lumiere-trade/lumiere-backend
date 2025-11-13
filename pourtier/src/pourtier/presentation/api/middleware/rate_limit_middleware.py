"""
Rate Limiting Middleware for FastAPI.

Applies rate limits per user/IP and adds rate limit headers to responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container
from pourtier.infrastructure.rate_limiting.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Features:
    - Per-user rate limiting (authenticated requests)
    - Per-IP rate limiting (unauthenticated requests)
    - Standard rate limit headers (X-RateLimit-*)
    - 429 Too Many Requests response
    - Configurable per-endpoint limits
    """

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.settings = get_settings()
        self.container = get_container()

        # Initialize rate limiter if Redis enabled AND connected
        if (
            self.settings.REDIS_ENABLED
            and self.container._cache_client is not None
            and hasattr(self.container._cache_client, "_client")
            and self.container._cache_client._client is not None
        ):
            # Convert requests per second to requests per minute
            rpm = int(self.settings.RATE_LIMIT_REQUESTS_PER_SECOND * 60)

            self.rate_limiter = RateLimiter(
                cache_client=self.container.cache_client,
                default_requests_per_minute=rpm,
                default_burst_size=self.settings.RATE_LIMIT_BURST_SIZE,
            )
        else:
            self.rate_limiter = None

        # Endpoints exempt from rate limiting
        self.exempt_endpoints = {
            "/",
            "/health",
            "/api/health",
            "/api/health/live",
            "/api/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response with rate limit headers
        """
        # Skip if rate limiting disabled or endpoint exempt
        if not self.rate_limiter or request.url.path in self.exempt_endpoints:
            return await call_next(request)

        # Get identifier (user_id or IP)
        identifier = self._get_identifier(request)

        # Get endpoint for rate limit tracking
        endpoint = self._normalize_endpoint(request.url.path)

        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
        )

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
        }

        if not allowed:
            # Rate limit exceeded
            headers["Retry-After"] = str(info["retry_after"])

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "limit": info["limit"],
                    "reset": info["reset"],
                    "retry_after": info["retry_after"],
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _get_identifier(self, request: Request) -> str:
        """
        Get identifier for rate limiting.

        Priority:
        1. User ID from auth (if authenticated)
        2. IP address (if unauthenticated)

        Args:
            request: FastAPI request

        Returns:
            Identifier string
        """
        # Try to get user_id from state (set by auth middleware)
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        # Check X-Forwarded-For header (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (client IP)
            ip = forwarded_for.split(",")[0].strip()
        else:
            # Direct connection
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint for rate limit tracking.

        Groups similar endpoints together.

        Args:
            path: Request path

        Returns:
            Normalized endpoint string
        """
        # Remove trailing slash
        path = path.rstrip("/")

        # Simple normalization
        # Replace UUID-like segments with :id
        segments = path.split("/")
        normalized = []

        for segment in segments:
            # Check if segment looks like UUID or numeric ID
            if (
                len(segment) == 36
                and segment.count("-") == 4  # UUID
                or segment.isdigit()  # Numeric ID
            ):
                normalized.append(":id")
            else:
                normalized.append(segment)

        return "/".join(normalized)
