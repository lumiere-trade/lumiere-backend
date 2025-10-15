"""
Escrow contract client service interface.

Defines operations for interacting with the Solana escrow smart contract.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pourtier.domain.value_objects.wallet_address import WalletAddress


class IEscrowContractClient(ABC):
    """
    Abstract service interface for Solana escrow contract interaction.

    Manages escrow accounts and trading authority delegation:
    - Initialize escrow PDA
    - Deposit funds to escrow
    - Approve trading destinations
    - Delegate trading authority to platform
    - Revoke authority (emergency stop)
    - Withdraw funds back to user
    - Close escrow account
    """

    @abstractmethod
    async def initialize_escrow(
        self,
        user_wallet: WalletAddress,
        strategy_id: UUID,
        token_mint: str,
        max_balance: Optional[int] = None,
    ) -> str:
        """
        Initialize escrow PDA for user and strategy.

        Args:
            user_wallet: User's Solana wallet address
            strategy_id: Strategy unique identifier (UUID)
            token_mint: Token mint address (e.g., USDC mint)
            max_balance: Optional maximum balance limit (in token units)

        Returns:
            Escrow account address (PDA)

        Raises:
            ContractError: If initialization fails
        """

    @abstractmethod
    async def deposit_funds(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
        token_mint: str,
    ) -> str:
        """
        Deposit funds from user wallet to escrow account.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Deposit amount in tokens
            token_mint: Token mint address (USDC, SOL, etc.)

        Returns:
            Transaction signature

        Raises:
            ContractError: If deposit fails
        """

    @abstractmethod
    async def approve_destination(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        destination: str,
    ) -> str:
        """
        Approve a destination token account for trading.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            destination: Destination token account address

        Returns:
            Transaction signature

        Raises:
            ContractError: If approval fails
        """

    @abstractmethod
    async def revoke_destination(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        destination: str,
    ) -> str:
        """
        Revoke approval for a destination token account.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            destination: Destination token account address

        Returns:
            Transaction signature

        Raises:
            ContractError: If revocation fails
        """

    @abstractmethod
    async def delegate_authority(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        trading_wallet: WalletAddress,
    ) -> str:
        """
        Delegate trading authority to platform wallet.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            trading_wallet: Platform trading wallet address

        Returns:
            Transaction signature

        Raises:
            ContractError: If delegation fails
        """

    @abstractmethod
    async def revoke_authority(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> str:
        """
        Revoke trading authority (emergency stop).

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Transaction signature

        Raises:
            ContractError: If revocation fails
        """

    @abstractmethod
    async def withdraw_funds(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
    ) -> str:
        """
        Withdraw funds from escrow back to user wallet.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Withdrawal amount (in token units)

        Returns:
            Transaction signature

        Raises:
            ContractError: If withdrawal fails
        """

    @abstractmethod
    async def pause_escrow(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> str:
        """
        Pause escrow account (emergency stop).

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Transaction signature

        Raises:
            ContractError: If pause fails
        """

    @abstractmethod
    async def unpause_escrow(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> str:
        """
        Unpause escrow account.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Transaction signature

        Raises:
            ContractError: If unpause fails
        """

    @abstractmethod
    async def close_escrow(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> str:
        """
        Close escrow account and recover rent.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Transaction signature

        Raises:
            ContractError: If close fails
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
    async def get_escrow_state(self, escrow_account: str) -> dict:
        """
        Query escrow account state.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with escrow state (authority, flags, etc.)

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
