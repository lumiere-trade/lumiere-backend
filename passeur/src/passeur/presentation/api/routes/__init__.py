"""
API routes module.

Exports all route routers for registration in main app.
"""

from passeur.presentation.api.routes.escrow import router as escrow_router
from passeur.presentation.api.routes.health import router as health_router
from passeur.presentation.api.routes.transaction import router as transaction_router
from passeur.presentation.api.routes.wallet import router as wallet_router

__all__ = [
    "health_router",
    "escrow_router",
    "transaction_router",
    "wallet_router",
]
