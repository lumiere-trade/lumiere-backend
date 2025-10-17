"""
Solana smart contract client adapter.

Handles escrow account management and fund delegation via Escrow Bridge.
"""

import asyncio
from decimal import Decimal
from typing import Optional
from uuid import UUID

import aiohttp

from pourtier.domain.services.i_escrow_contract_client import (
    IEscrowContractClient,
)
from pourtier.domain.value_objects.wallet_address import WalletAddress


class EscrowContractClient(IEscrowContractClient):
    """
    Solana smart contract client for escrow management.

    Communicates with Escrow Bridge API for blockchain interactions.
    """

    def __init__(
        self,
        bridge_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize escrow contract client.

        Args:
            bridge_url: Escrow Bridge API base URL (if None, loaded from config)
            timeout: HTTP request timeout in seconds
        """
        # Load from config if not provided
        if bridge_url is None:
            from pourtier.config.settings import get_settings
            settings = get_settings()
            bridge_url = settings.passeur_url
        
        self.bridge_url = bridge_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

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
            strategy_id: Strategy unique identifier
            token_mint: Token mint address (e.g., USDC mint)
            max_balance: Optional maximum balance limit

        Returns:
            Escrow account address (PDA)

        Raises:
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "strategyId": str(strategy_id),
            "tokenMint": token_mint,
        }

        if max_balance is not None:
            payload["maxBalance"] = max_balance

        async with session.post(
            f"{self.bridge_url}/escrow/initialize", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to initialize escrow: {error_text}")

            data = await response.json()
            return data["escrowAccount"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
            "amount": str(amount),
            "tokenMint": token_mint,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/deposit", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to deposit funds: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
            "destination": destination,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/approve-destination",
            json=payload,
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to approve destination: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
            "destination": destination,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/revoke-destination", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to revoke destination: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
            "authority": trading_wallet.address,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/delegate", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to delegate authority: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/revoke", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to revoke authority: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
            "amount": str(amount),
        }

        async with session.post(
            f"{self.bridge_url}/escrow/withdraw", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to withdraw funds: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/pause", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to pause escrow: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/unpause", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to unpause escrow: {error_text}")

            data = await response.json()
            return data["signature"]

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
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        payload = {
            "userWallet": user_wallet.address,
            "escrowAccount": escrow_account,
        }

        async with session.post(
            f"{self.bridge_url}/escrow/close", json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to close escrow: {error_text}")

            data = await response.json()
            return data["signature"]

    async def get_escrow_balance(self, escrow_account: str) -> Decimal:
        """
        Query current balance in escrow account.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Current balance in token units

        Raises:
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        async with session.get(
            f"{self.bridge_url}/escrow/balance/{escrow_account}"
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get escrow balance: {error_text}")

            data = await response.json()
            return Decimal(str(data["balance"]))

    async def get_escrow_state(self, escrow_account: str) -> dict:
        """
        Query escrow account state.

        Args:
            escrow_account: Escrow PDA address

        Returns:
            Dictionary with escrow state (authority, flags, etc.)

        Raises:
            Exception: If Bridge API call fails
        """
        session = await self._get_session()

        async with session.get(
            f"{self.bridge_url}/escrow/state/{escrow_account}"
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get escrow state: {error_text}")

            return await response.json()

    async def confirm_transaction(
        self, tx_signature: str, max_retries: int = 30
    ) -> bool:
        """
        Wait for transaction confirmation on-chain.

        Args:
            tx_signature: Transaction signature to confirm
            max_retries: Maximum number of confirmation attempts

        Returns:
            True if confirmed, False if failed/timeout
        """
        session = await self._get_session()

        for attempt in range(max_retries):
            try:
                async with session.get(
                    f"{self.bridge_url}/transaction/status/{tx_signature}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["confirmed"]:
                            return True

                    await asyncio.sleep(2)

            except Exception:
                await asyncio.sleep(2)
                continue

        return False

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
