"""
Blockchain transaction verifier interface.

Defines operations for verifying and parsing blockchain transactions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class VerifiedTransaction:
    """
    Parsed and verified blockchain transaction data.

    Contains essential transaction information after verification.
    """

    signature: str
    is_confirmed: bool
    sender: str
    recipient: Optional[str]
    amount: Optional[Decimal]
    token_mint: Optional[str]
    block_time: Optional[int]
    slot: Optional[int]


class IBlockchainVerifier(ABC):
    """
    Abstract interface for blockchain transaction verification.

    Verifies user-signed transactions on Solana blockchain
    without requiring signing capabilities.
    """

    @abstractmethod
    async def verify_transaction(
        self,
        tx_signature: str,
    ) -> VerifiedTransaction:
        """
        Verify transaction exists on blockchain and parse data.

        Args:
            tx_signature: Transaction signature to verify

        Returns:
            VerifiedTransaction with parsed transaction details

        Raises:
            TransactionNotFoundError: If transaction not found
            TransactionNotConfirmedError: If transaction not confirmed
        """

    @abstractmethod
    async def wait_for_confirmation(
        self,
        tx_signature: str,
        max_retries: int = 30,
    ) -> bool:
        """
        Wait for transaction confirmation on blockchain.

        Args:
            tx_signature: Transaction signature to monitor
            max_retries: Maximum confirmation attempts (default: 30)

        Returns:
            True if confirmed, False if timeout
        """
