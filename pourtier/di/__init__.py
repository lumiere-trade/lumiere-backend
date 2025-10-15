"""
Dependency Injection module for Pourtier.

Provides container and dependency functions for FastAPI routes.
"""

from pourtier.di.container import (
    DIContainer,
    get_container,
    initialize_container,
    shutdown_container,
)
from pourtier.di.dependencies import (
    get_accept_legal_documents,
    get_check_user_legal_compliance,
    get_create_subscription,
    get_create_user,
    get_create_user_with_legal,
    get_db_session,
    get_deposit_to_escrow,
    get_get_active_legal_documents,
    get_get_escrow_balance,
    get_get_user_by_wallet,
    get_get_user_profile,
    get_initialize_escrow,
    get_login_user,
    get_verify_wallet_signature,
    get_wallet_authenticator,
    get_withdraw_from_escrow,
)

__all__ = [
    # Container
    "DIContainer",
    "get_container",
    "initialize_container",
    "shutdown_container",
    # Dependencies
    "get_db_session",
    "get_create_user",
    "get_get_user_profile",
    "get_get_user_by_wallet",
    "get_create_user_with_legal",
    "get_login_user",
    "get_verify_wallet_signature",
    "get_wallet_authenticator",
    "get_create_subscription",
    "get_initialize_escrow",
    "get_deposit_to_escrow",
    "get_withdraw_from_escrow",
    "get_get_escrow_balance",
    "get_get_active_legal_documents",
    "get_check_user_legal_compliance",
    "get_accept_legal_documents",
]
