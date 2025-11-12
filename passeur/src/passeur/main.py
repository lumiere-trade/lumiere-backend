"""
Passeur main application.

FastAPI application with resilience patterns:
- Health checks (Kubernetes-compatible)
- Metrics (Prometheus)
- Graceful shutdown
- Circuit breakers
- Idempotency
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.health import HealthServer
from shared.observability import MetricsServer

from passeur.config.settings import get_settings
from passeur.infrastructure.blockchain.bridge_client import BridgeClient
from passeur.infrastructure.blockchain.solana_rpc_client import SolanaRPCClient
from passeur.infrastructure.blockchain.transaction_manager import (
    TransactionManager,
)
from passeur.infrastructure.cache.redis_idempotency_store import (
    RedisIdempotencyStore,
)
from passeur.infrastructure.monitoring.graceful_shutdown import (
    PasseurGracefulShutdown,
)
from passeur.infrastructure.monitoring.passeur_health_checker import (
    PasseurHealthChecker,
)
from passeur.presentation.api.routes import health_router
from passeur.presentation.api.routes.health import set_health_checker

# Global instances
settings = get_settings()
shutdown_handler: PasseurGracefulShutdown = None
health_server: HealthServer = None
metrics_server: MetricsServer = None
redis_store: RedisIdempotencyStore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown:
    - Initialize Redis
    - Start health server
    - Start metrics server
    - Setup graceful shutdown
    """
    global shutdown_handler, health_server, metrics_server, redis_store

    # Startup
    print("Starting Passeur...")

    # Initialize Redis idempotency store
    redis_store = RedisIdempotencyStore()
    print(
        f"Redis idempotency store initialized: {
            settings.redis.host}:{
            settings.redis.port}"
    )

    # Initialize clients
    rpc_client = SolanaRPCClient()
    bridge_client = BridgeClient()
    transaction_manager = TransactionManager(
        bridge_client=bridge_client,
        rpc_client=rpc_client,
        idempotency_store=redis_store,
    )

    # Store in app state
    app.state.rpc_client = rpc_client
    app.state.bridge_client = bridge_client
    app.state.transaction_manager = transaction_manager
    app.state.redis_store = redis_store

    # Health checker
    health_checker = PasseurHealthChecker(
        redis_client=redis_store.redis if hasattr(redis_store, "redis") else None,
    )
    set_health_checker(health_checker)

    # Start health server
    if settings.health.port:
        health_server = HealthServer(health_checker, port=settings.health.port)
        health_server.start_in_background()
        print(f"Health server started on port {settings.health.port}")

    # Start metrics server
    if settings.metrics.enabled and settings.metrics.port:
        metrics_server = MetricsServer(
            host="0.0.0.0",
            port=settings.metrics.port,
        )
        metrics_server.start_in_background()
        print(f"Metrics server started on port {settings.metrics.port}")

    # Setup graceful shutdown
    shutdown_handler = PasseurGracefulShutdown(timeout=30.0)

    async def cleanup_redis():
        if redis_store:
            await redis_store.close()
            print("Redis connection closed")

    shutdown_handler.register_cleanup(cleanup_redis)

    print(f"Passeur started successfully on port {settings.api_port}")
    print(f"Health checks: http://localhost:{settings.health.port}/health")
    print(f"Metrics: http://localhost:{settings.metrics.port}/metrics")

    yield

    # Shutdown
    print("Shutting down Passeur...")

    if shutdown_handler:
        await shutdown_handler.shutdown()

    print("Passeur stopped")


# Create FastAPI app
app = FastAPI(
    title="Passeur - Blockchain Bridge",
    description="Solana blockchain bridge with resilience patterns",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "passeur",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "metrics": f"http://localhost:{settings.metrics.port}/metrics",
        },
    }


def main():
    """
    Main entry point.

    Run with: python -m passeur.main
    Or: uvicorn passeur.main:app --host 0.0.0.0 --port 8766
    """
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
