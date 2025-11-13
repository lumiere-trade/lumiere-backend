"""
Escrow contract client service interface.

Defines operations for interacting with the Solana escrow smart contract.
Uses prepare-sign-submit pattern for security (backend never touches
private keys).
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from pourtier.domain.value_objects.wallet_address import WalletAddress


class IEscrowContractClient(ABC):
    """
    Abstract service interface for Solana escrow contract interaction.

    NEW ARCHITECTURE (Passeur Phase 2):
    - User-based escrow (no strategy_id)
    - Prepare-sign-submit pattern
    - Returns unsigned transactions for frontend signing
    - Separate platform and trading authority delegation

    Manages escrow accounts and trading authority delegation:
    - Prepare initialize escrow PDA transaction
    - Prepare deposit funds transaction
    - Prepare delegate authority transactions (platform/trading)
    - Prepare revoke authority transactions (platform/trading)
    - Prepare withdraw funds transaction
    - Prepare close escrow account transaction
    - Submit signed transactions
    - Query escrow balance and details
    """

    @abstractmethod
    async def prepare_initialize_escrow(
        self,
        user_wallet: WalletAddress,
        max_balance: Optional[int] = None,
    ) -> dict:
        """
        Prepare unsigned transaction to initialize escrow PDA.

        Note: User-based escrow (no strategy_id). One escrow per user.
        PDA derivation: seeds = [b"escrow", bytes(user_pubkey)]

        Args:
            user_wallet: User's Solana wallet address
            max_balance: Optional maximum balance limit (in token units)

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction),
                "escrowAccount": str (PDA address),
                "bump": int
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_deposit(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
    ) -> dict:
        """
        Prepare unsigned transaction to deposit funds to escrow.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Deposit amount in tokens

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction),
                "amount": str
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_delegate_platform(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        platform_authority: WalletAddress,
    ) -> dict:
        """
        Prepare unsigned transaction to delegate platform authority.

        Platform authority can manage escrow configuration.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            platform_authority: Platform authority wallet address

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction)
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_delegate_trading(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        trading_authority: WalletAddress,
    ) -> dict:
        """
        Prepare unsigned transaction to delegate trading authority.

        Trading authority can execute trades from escrow.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            trading_authority: Trading authority wallet address

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction)
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_revoke_platform(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to revoke platform authority.

        Emergency stop for platform access.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction)
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_revoke_trading(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to revoke trading authority.

        Emergency stop for trading.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction)
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_withdraw(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
    ) -> dict:
        """
        Prepare unsigned transaction to withdraw funds from escrow.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Withdrawal amount (in token units)

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction),
                "amount": str
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def prepare_close(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to close escrow account.

        Recovers rent from closed account.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with:
            {
                "transaction": str (base64 unsigned transaction)
            }

        Raises:
            ContractError: If preparation fails
        """

    @abstractmethod
    async def submit_signed_transaction(
        self,
        signed_transaction: str,
    ) -> str:
        """
        Submit signed transaction to blockchain.

        Args:
            signed_transaction: Base64-encoded signed transaction
                (signed by user in frontend)

        Returns:
            Transaction signature (hash)

        Raises:
            ContractError: If submission fails
        """

    @abstractmethod
    async def get_escrow_balance(self, escrow_account: str) -> Decimal:
        """
        Query current balance in escrow token account.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Current balance in token units

        Raises:
            ContractError: If query fails
        """

    @abstractmethod
    async def get_escrow_details(self, escrow_account: str) -> dict:
        """
        Query escrow account details.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with escrow state (authority, flags, balance, etc.)

        Raises:
            ContractError: If query fails
        """

    @abstractmethod
    async def confirm_transaction(
        self,
        tx_signature: str,
        max_retries: int = 30,
    ) -> bool:
        """
        Wait for transaction confirmation on-chain.

        Args:
            tx_signature: Transaction signature to confirm
            max_retries: Maximum number of confirmation attempts

        Returns:
            True if confirmed, False if failed/timeout
        """
