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
    pass


class TransactionException(BlockchainException):
    """Transaction failed."""
    pass


class TransactionTimeoutException(TransactionException):
    """Transaction confirmation timeout."""
    pass


class InsufficientFundsException(BlockchainException):
    """Insufficient funds for operation."""
    pass


class InvalidTransactionException(BlockchainException):
    """Transaction validation failed."""
    pass
