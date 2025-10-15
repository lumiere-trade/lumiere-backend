"""
Payment-related domain exceptions.
"""

from pourtier.domain.exceptions.base import PourtierException


class InsufficientFundsError(PourtierException):
    """Raised when user has insufficient escrow funds."""

    def __init__(self, message: str = "Insufficient escrow balance"):
        super().__init__(message, code="INSUFFICIENT_FUNDS")
