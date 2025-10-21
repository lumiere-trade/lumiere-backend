"""
Main FastAPI application entry point.

Uses Application Factory Pattern for proper dependency injection
and testability.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pourtier.config.settings import Settings, get_settings
from pourtier.di import get_container, initialize_container, shutdown_container
from pourtier.domain.exceptions import PourtierException
from pourtier.infrastructure.cache import ResponseCache
from pourtier.infrastructure.monitoring import get_logger, setup_logging
from pourtier.presentation.api.middleware import (
    pourtier_exception_handler,
)
from pourtier.presentation.api.middleware.metrics_middleware import (
    MetricsMiddleware,
)
from pourtier.presentation.api.middleware.request_id_middleware import (
    RequestIDMiddleware,
)
from pourtier.presentation.api.routes import (
    auth,
    escrow,
    legal,
    subscriptions,
    users,
)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Application factory - creates and configures FastAPI app.

    Args:
        settings: Optional Settings instance (for testing)

    Returns:
        Configured FastAPI application
    """
    # Get or use provided settings
    if settings is None:
        settings = get_settings()

    # Setup structured logging (JSON only in production)
    json_logs = settings.ENV == "production"
    setup_logging(level=settings.LOG_LEVEL, json_logs=json_logs)
    logger = get_logger(__name__)

    logger.info(f"Creating Pourtier application (ENV={settings.ENV})")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        # Startup
        logger.info("Starting Pourtier application...")
        await initialize_container()

        # Initialize response cache if Redis enabled
        if settings.REDIS_ENABLED:
            container = get_container()
            response_cache = ResponseCache(
                redis_client=container.cache_client, default_ttl=300
            )
            app.state.response_cache = response_cache
            logger.info("Response cache initialized")

        logger.info("Pourtier application started successfully")

        yield

        # Shutdown
        logger.info("Shutting down Pourtier application...")
        await shutdown_container()
        logger.info("Pourtier application shutdown complete")

    # Create FastAPI app
    app = FastAPI(
        title="Pourtier API",
        description="Escrow-based subscription billing for Lumiere DeFi",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Request ID middleware (add FIRST for tracking)
    app.add_middleware(RequestIDMiddleware)

    # Metrics middleware (add SECOND for accurate timing)
    app.add_middleware(MetricsMiddleware)

    # GZip compression middleware (add before CORS for correct order)
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
        compresslevel=6,
    )

    # CORS middleware - configured via settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(PourtierException, pourtier_exception_handler)

    # Register routes
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(subscriptions.router, prefix="/api")
    app.include_router(escrow.router, prefix="/api")
    app.include_router(legal.router, prefix="/api")

    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint."""
        return {
            "service": "Pourtier",
            "status": "running",
            "version": "0.1.0",
            "description": "Escrow-based subscription billing",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Comprehensive health check endpoint.

        Returns detailed status of all components.
        """
        container = get_container()

        # Check database
        db_healthy = await container.database.health_check()

        # Check Redis (if enabled)
        redis_healthy = False
        redis_info = "disabled"
        if settings.REDIS_ENABLED:
            try:
                await container.cache_client.ping()
                redis_healthy = True
                redis_info = "connected"
            except Exception as e:
                redis_info = f"error: {str(e)}"

        # Check database pool stats
        pool_stats = {}
        if hasattr(container.database, "_engine") and container.database._engine:
            pool = container.database._engine.pool
            pool_stats = {
                "size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "checked_in": pool.checkedin(),
            }

        # Determine overall status
        components_healthy = db_healthy and (
            redis_healthy or not settings.REDIS_ENABLED
        )
        overall_status = "healthy" if components_healthy else "degraded"

        return {
            "status": overall_status,
            "version": "0.1.0",
            "components": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "pool": pool_stats,
                },
                "cache": {
                    "status": "healthy" if redis_healthy else "unavailable",
                    "info": redis_info,
                    "enabled": settings.REDIS_ENABLED,
                },
            },
            "timestamp": "now",
        }

    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """
        Prometheus metrics endpoint.

        Returns metrics in Prometheus text format for scraping.
        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    logger.info("Pourtier application created successfully")
    return app


def get_app() -> FastAPI:
    """
    Get or create application instance (lazy initialization).

    For uvicorn: uvicorn pourtier.main:get_app --factory
    """
    return create_app()


# For backwards compatibility with: uvicorn pourtier.main:app
# This will be created on first access by uvicorn
app: Optional[FastAPI] = None


def __getattr__(name: str):
    """Module-level __getattr__ for lazy app initialization."""
    global app
    if name == "app":
        if app is None:
            app = create_app()
        return app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def main():
    """Run the application with uvicorn."""
    import uvicorn

    # Use factory mode for proper lazy initialization
    settings = get_settings()
    uvicorn.run(
        "pourtier.main:get_app",
        factory=True,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )


if __name__ == "__main__":
    main()
