"""
Passeur Bridge interface.

Defines operations for preparing unsigned blockchain transactions.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID


class IPasseurBridge(ABC):
    """
    Abstract interface for Passeur Bridge communication.

    Prepares unsigned transactions for user signing in frontend.
    Does NOT sign transactions - that's user's responsibility.
    """

    @abstractmethod
    async def prepare_initialize_escrow(
        self,
        user_wallet: str,
        token_mint: str,
        strategy_id: UUID,
    ) -> str:
        """
        Prepare initialize escrow transaction.

        Args:
            user_wallet: User's Solana wallet address
            token_mint: Token mint address (e.g., USDC)
            strategy_id: Strategy unique identifier

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_deposit(
        self,
        user_wallet: str,
        escrow_account: str,
        amount: Decimal,
    ) -> str:
        """
        Prepare deposit transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Deposit amount in tokens

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_withdraw(
        self,
        user_wallet: str,
        escrow_account: str,
        amount: Decimal,
    ) -> str:
        """
        Prepare withdraw transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Withdrawal amount in tokens

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """
