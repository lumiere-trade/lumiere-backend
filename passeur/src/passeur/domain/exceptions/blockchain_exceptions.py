"""
Blockchain-related exceptions.
"""

from typing import Optional


class BlockchainException(Exception):
    """Base exception for blockchain operations."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class RPCException(BlockchainException):
    """RPC call failed."""


class TransactionException(BlockchainException):
    """Transaction failed."""


class TransactionTimeoutException(TransactionException):
    """Transaction confirmation timeout."""


class InsufficientFundsException(BlockchainException):
    """Insufficient funds for operation."""


class InvalidTransactionException(BlockchainException):
    """Transaction validation failed."""
