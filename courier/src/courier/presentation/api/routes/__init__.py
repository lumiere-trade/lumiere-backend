"""
API routes for Courier.
"""

from courier.presentation.api.routes.health import router as health_router
from courier.presentation.api.routes.publish import router as publish_router
from courier.presentation.api.routes.stats import router as stats_router
from courier.presentation.api.routes.websocket import router as websocket_router

__all__ = ["health_router", "publish_router", "stats_router", "websocket_router"]
