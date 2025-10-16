"""
Blockchain-related exceptions.

Defines exceptions for blockchain and escrow operations.
"""

from pourtier.domain.exceptions.base import PourtierException


class BlockchainError(PourtierException):
    """Base exception for blockchain operations."""


class BridgeError(BlockchainError):
    """Raised when Passeur Bridge API call fails."""

    def __init__(self, message: str, status_code: int = None):
        """
        Initialize bridge error.

        Args:
            message: Error message
            status_code: HTTP status code from Bridge API
        """
        super().__init__(message)
        self.status_code = status_code


class TransactionNotFoundError(BlockchainError):
    """Raised when transaction not found on blockchain."""

    def __init__(self, tx_signature: str):
        """
        Initialize transaction not found error.

        Args:
            tx_signature: Transaction signature that was not found
        """
        super().__init__(f"Transaction not found: {tx_signature}")
        self.tx_signature = tx_signature


class TransactionNotConfirmedError(BlockchainError):
    """Raised when transaction not confirmed on blockchain."""

    def __init__(self, tx_signature: str):
        """
        Initialize transaction not confirmed error.

        Args:
            tx_signature: Transaction signature not confirmed
        """
        super().__init__(f"Transaction not confirmed: {tx_signature}")
        self.tx_signature = tx_signature


class EscrowNotFoundError(BlockchainError):
    """Raised when escrow account not found on blockchain."""

    def __init__(self, escrow_account: str):
        """
        Initialize escrow not found error.

        Args:
            escrow_account: Escrow account address not found
        """
        super().__init__(f"Escrow account not found: {escrow_account}")
        self.escrow_account = escrow_account


class EscrowAlreadyInitializedError(BlockchainError):
    """Raised when attempting to initialize already initialized escrow."""

    def __init__(self, user_id: str):
        """
        Initialize escrow already initialized error.

        Args:
            user_id: User ID with existing escrow
        """
        super().__init__(f"User {user_id} already has initialized escrow")
        self.user_id = user_id


class InsufficientEscrowBalanceError(BlockchainError):
    """Raised when user has insufficient escrow balance."""

    def __init__(self, required: str, available: str):
        """
        Initialize insufficient balance error.

        Args:
            required: Required amount
            available: Available balance
        """
        super().__init__(
            f"Insufficient escrow balance: required {required}, "
            f"available {available}"
        )
        self.required = required
        self.available = available


class InvalidTransactionError(BlockchainError):
    """Raised when transaction data is invalid or malformed."""

    def __init__(self, message: str, tx_signature: str = None):
        """
        Initialize invalid transaction error.

        Args:
            message: Error description
            tx_signature: Optional transaction signature
        """
        super().__init__(message)
        self.tx_signature = tx_signature
