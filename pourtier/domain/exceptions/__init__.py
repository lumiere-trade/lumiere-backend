"""
Domain exceptions package.
"""

# Auth exceptions
from pourtier.domain.exceptions.auth import (
    ExpiredTokenError,
    InvalidSignatureError,
    InvalidTokenError,
)

# Base exceptions
from pourtier.domain.exceptions.base import (
    DuplicateEntityError,
    EntityNotFoundError,
    PourtierException,
    ValidationError,
)

# Blockchain exceptions
from pourtier.domain.exceptions.blockchain import (
    BlockchainError,
    BridgeError,
    EscrowAlreadyInitializedError,
    EscrowNotFoundError,
    InsufficientEscrowBalanceError,
    InvalidTransactionError,
    TransactionNotConfirmedError,
    TransactionNotFoundError,
)

# Deployment exceptions
from pourtier.domain.exceptions.deployment import (
    DeploymentAlreadyActiveError,
    DeploymentError,
    InvalidDeploymentStateError,
    StrategyNotFoundError,
)

# Payment exceptions
from pourtier.domain.exceptions.payment import InsufficientFundsError

# Subscription exceptions
from pourtier.domain.exceptions.subscription import (
    NoActiveSubscriptionError,
    SubscriptionError,
    SubscriptionExpiredError,
    SubscriptionLimitExceededError,
)

__all__ = [
    # Base
    "PourtierException",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    # Auth
    "InvalidSignatureError",
    "InvalidTokenError",
    "ExpiredTokenError",
    # Blockchain
    "BlockchainError",
    "BridgeError",
    "TransactionNotFoundError",
    "TransactionNotConfirmedError",
    "InvalidTransactionError",
    "EscrowAlreadyInitializedError",
    "EscrowNotFoundError",
    "InsufficientEscrowBalanceError",
    # Subscription
    "SubscriptionError",
    "SubscriptionExpiredError",
    "SubscriptionLimitExceededError",
    "NoActiveSubscriptionError",
    # Deployment
    "DeploymentError",
    "StrategyNotFoundError",
    "DeploymentAlreadyActiveError",
    "InvalidDeploymentStateError",
    # Payment
    "InsufficientFundsError",
]
