"""
Passeur Bridge interface.

Defines operations for preparing unsigned blockchain transactions and querying blockchain state.
"""

from abc import ABC, abstractmethod
from decimal import Decimal


class IPasseurBridge(ABC):
    """
    Abstract interface for Passeur Bridge communication.

    Prepares unsigned transactions for user signing in frontend.
    Queries wallet and escrow balances from blockchain.
    Does NOT sign transactions - that is user's responsibility.
    """

    @abstractmethod
    async def prepare_initialize_escrow(
        self,
        user_wallet: str,
        token_mint: str = "USDC",
    ) -> str:
        """
        Prepare initialize escrow transaction.

        Args:
            user_wallet: User's Solana wallet address
            token_mint: Token mint address (default: USDC)

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

    @abstractmethod
    async def get_wallet_balance(
        self,
        wallet_address: str,
    ) -> Decimal:
        """
        Get USDC balance in user's Solana wallet (not escrow).

        Args:
            wallet_address: Solana wallet address to query

        Returns:
            USDC balance as Decimal

        Raises:
            BridgeError: If Bridge API call fails
        """
