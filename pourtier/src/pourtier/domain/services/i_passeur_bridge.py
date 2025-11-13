"""
Passeur Bridge interface.

Defines operations for preparing unsigned blockchain transactions and
querying blockchain state.
"""

from abc import ABC, abstractmethod
from decimal import Decimal


class IPasseurBridge(ABC):
    """
    Abstract interface for Passeur Bridge communication.

    Prepares unsigned transactions for user signing in frontend.
    Submits signed transactions to Solana blockchain.
    Queries wallet and escrow balances from blockchain.
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
    async def submit_signed_transaction(
        self,
        signed_transaction: str,
    ) -> str:
        """
        Submit signed transaction to Solana blockchain.

        Args:
            signed_transaction: Base64-encoded signed transaction

        Returns:
            Transaction signature (hash) from blockchain

        Raises:
            BridgeError: If submission fails
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
    async def prepare_delegate_platform(
        self,
        user_wallet: str,
        escrow_account: str,
        platform_authority: str,
    ) -> str:
        """
        Prepare delegate platform authority transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            platform_authority: Platform authority wallet address

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_delegate_trading(
        self,
        user_wallet: str,
        escrow_account: str,
        trading_authority: str,
    ) -> str:
        """
        Prepare delegate trading authority transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            trading_authority: Trading authority wallet address

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_revoke_platform(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> str:
        """
        Prepare revoke platform authority transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_revoke_trading(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> str:
        """
        Prepare revoke trading authority transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def prepare_close(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> str:
        """
        Prepare close escrow account transaction.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Unsigned transaction (base64) for user to sign

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def get_escrow_balance(
        self,
        escrow_account: str,
    ) -> Decimal:
        """
        Get escrow account balance.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Balance as Decimal

        Raises:
            BridgeError: If Bridge API call fails
        """

    @abstractmethod
    async def get_escrow_details(
        self,
        escrow_account: str,
    ) -> dict:
        """
        Get escrow account details.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with escrow details

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
