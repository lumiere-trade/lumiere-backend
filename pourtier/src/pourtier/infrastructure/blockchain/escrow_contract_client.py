"""
Solana smart contract client adapter.

Handles escrow account management and fund delegation via Passeur Bridge.
Uses PasseurBridgeClient for all blockchain interactions.
"""

from decimal import Decimal
from typing import Optional

from pourtier.domain.services.i_escrow_contract_client import (
    IEscrowContractClient,
)
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.domain.value_objects.wallet_address import WalletAddress


class EscrowContractClient(IEscrowContractClient):
    """
    Solana smart contract client for escrow management.

    Delegates all blockchain operations to PasseurBridgeClient.
    Provides domain-level interface for escrow operations.
    """

    def __init__(self, passeur_bridge: IPasseurBridge):
        """
        Initialize escrow contract client.

        Args:
            passeur_bridge: PasseurBridgeClient instance
        """
        self.bridge = passeur_bridge

    async def prepare_initialize_escrow(
        self,
        user_wallet: WalletAddress,
        max_balance: Optional[int] = None,
    ) -> dict:
        """
        Prepare unsigned transaction to initialize escrow PDA.

        Args:
            user_wallet: User's Solana wallet address
            max_balance: Optional maximum balance limit

        Returns:
            Dictionary with unsigned transaction and escrow account address

        Raises:
            Exception: If Bridge API call fails
        """
        # Passeur expects string wallet address
        unsigned_tx = await self.bridge.prepare_initialize_escrow(
            user_wallet=user_wallet.address,
            token_mint="USDC",
        )

        # Return transaction for frontend signing
        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_deposit(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
    ) -> dict:
        """
        Prepare unsigned transaction to deposit funds.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Deposit amount in tokens

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_deposit(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
            amount=amount,
        )

        return {
            "transaction": unsigned_tx,
            "amount": str(amount),
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_delegate_platform(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        platform_authority: WalletAddress,
    ) -> dict:
        """
        Prepare unsigned transaction to delegate platform authority.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            platform_authority: Platform authority wallet address

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_delegate_platform(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
            platform_authority=platform_authority.address,
        )

        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_delegate_trading(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        trading_authority: WalletAddress,
    ) -> dict:
        """
        Prepare unsigned transaction to delegate trading authority.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            trading_authority: Trading authority wallet address

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_delegate_trading(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
            trading_authority=trading_authority.address,
        )

        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_revoke_platform(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to revoke platform authority.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_revoke_platform(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
        )

        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_revoke_trading(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to revoke trading authority.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_revoke_trading(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
        )

        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_withdraw(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
        amount: Decimal,
    ) -> dict:
        """
        Prepare unsigned transaction to withdraw funds.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address
            amount: Withdrawal amount

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_withdraw(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
            amount=amount,
        )

        return {
            "transaction": unsigned_tx,
            "amount": str(amount),
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def prepare_close(
        self,
        user_wallet: WalletAddress,
        escrow_account: str,
    ) -> dict:
        """
        Prepare unsigned transaction to close escrow account.

        Args:
            user_wallet: User's Solana wallet address
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with unsigned transaction

        Raises:
            Exception: If Bridge API call fails
        """
        unsigned_tx = await self.bridge.prepare_close(
            user_wallet=user_wallet.address,
            escrow_account=escrow_account,
        )

        return {
            "transaction": unsigned_tx,
            "message": "Transaction prepared. Please sign with your wallet.",
        }

    async def submit_signed_transaction(
        self,
        signed_transaction: str,
    ) -> str:
        """
        Submit signed transaction to blockchain.

        Args:
            signed_transaction: Base64-encoded signed transaction

        Returns:
            Transaction signature

        Raises:
            Exception: If submission fails
        """
        signature = await self.bridge.submit_signed_transaction(
            signed_transaction=signed_transaction
        )

        return signature

    async def get_escrow_balance(self, escrow_account: str) -> Decimal:
        """
        Query current balance in escrow account.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Current balance in token units

        Raises:
            Exception: If query fails
        """
        balance = await self.bridge.get_escrow_balance(
            escrow_account=escrow_account
        )

        return balance

    async def get_escrow_details(self, escrow_account: str) -> dict:
        """
        Query escrow account details.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with escrow state

        Raises:
            Exception: If query fails
        """
        details = await self.bridge.get_escrow_details(
            escrow_account=escrow_account
        )

        return details

    async def confirm_transaction(
        self, tx_signature: str, max_retries: int = 30
    ) -> bool:
        """
        Wait for transaction confirmation on-chain.

        Note: This is a placeholder. Real implementation would query
        Passeur or Solana RPC for transaction status.

        Args:
            tx_signature: Transaction signature to confirm
            max_retries: Maximum number of confirmation attempts

        Returns:
            True if confirmed, False if failed/timeout
        """
        # TODO: Implement via Passeur /transaction/status/{signature}
        # For now, assume success
        return True

    async def close(self) -> None:
        """Close underlying PasseurBridgeClient session."""
        await self.bridge.close()
