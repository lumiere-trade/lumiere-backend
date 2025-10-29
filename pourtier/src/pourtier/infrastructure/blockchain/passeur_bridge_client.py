"""
Passeur Bridge client implementation.

HTTP client for communicating with Passeur Bridge API.
"""

import asyncio
from decimal import Decimal
from typing import Optional

import aiohttp
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pourtier.domain.exceptions.blockchain import BridgeError
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge


class PasseurBridgeClient(IPasseurBridge):
    """
    Passeur Bridge HTTP client.

    Communicates with Passeur Bridge API to prepare unsigned
    blockchain transactions for user signing and query blockchain state.

    Includes retries and optimized timeouts for production reliability.
    """

    def __init__(
        self,
        bridge_url: str,
        total_timeout: int = 10,
        connect_timeout: int = 3,
        max_retries: int = 3,
    ):
        """
        Initialize Passeur Bridge client.

        Args:
            bridge_url: Passeur Bridge API base URL
            total_timeout: Total request timeout in seconds (default: 10s)
            connect_timeout: Connection timeout in seconds (default: 3s)
            max_retries: Max retry attempts for transient failures (default: 3)
        """
        self.bridge_url = bridge_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(
            total=total_timeout,
            connect=connect_timeout,
        )
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with optimized get_settings()."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=50,
                    limit_per_host=20,
                    ttl_dns_cache=300,
                ),
            )
        return self._session

    async def _make_request_with_retry(
        self,
        endpoint: str,
        payload: dict,
        operation: str,
    ) -> str:
        """
        Make HTTP request with automatic retries.

        Args:
            endpoint: API endpoint path
            payload: Request JSON payload
            operation: Operation name for error messages

        Returns:
            Transaction string from response

        Raises:
            BridgeError: If request fails after all retries
        """
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                retry=retry_if_exception_type(
                    (aiohttp.ClientError, asyncio.TimeoutError)
                ),
                reraise=True,
            ):
                with attempt:
                    return await self._make_request_once(endpoint, payload, operation)
        except RetryError:
            raise BridgeError(
                f"Bridge {operation} failed after {self.max_retries} retries"
            )

    async def _make_request_once(
        self,
        endpoint: str,
        payload: dict,
        operation: str,
    ) -> str:
        """
        Single HTTP request attempt (called by retry logic).

        Args:
            endpoint: API endpoint path
            payload: Request JSON payload
            operation: Operation name for error messages

        Returns:
            Transaction string from response

        Raises:
            BridgeError: If request fails
            aiohttp.ClientError: Network errors (will be retried)
        """
        session = await self._get_session()
        url = f"{self.bridge_url}{endpoint}"

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if 400 <= response.status < 500:
                        raise BridgeError(
                            f"Failed to {operation}: {error_text}",
                            status_code=response.status,
                        )
                    raise aiohttp.ClientError(
                        f"Server error {response.status}: {error_text}"
                    )

                data = await response.json()
                return data["transaction"]

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise

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
        payload = {
            "userWallet": user_wallet,
            "tokenMint": token_mint,
        }

        return await self._make_request_with_retry(
            endpoint="/escrow/prepare-initialize",
            payload=payload,
            operation="initialize escrow",
        )

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
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "amount": float(amount),
        }

        return await self._make_request_with_retry(
            endpoint="/escrow/prepare-deposit",
            payload=payload,
            operation="deposit",
        )

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
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "amount": float(amount),
        }

        return await self._make_request_with_retry(
            endpoint="/escrow/prepare-withdraw",
            payload=payload,
            operation="withdraw",
        )

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
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                retry=retry_if_exception_type(
                    (aiohttp.ClientError, asyncio.TimeoutError)
                ),
                reraise=True,
            ):
                with attempt:
                    return await self._get_wallet_balance_once(wallet_address)
        except RetryError:
            raise BridgeError(
                f"Failed to get wallet balance after {self.max_retries} retries"
            )

    async def _get_wallet_balance_once(self, wallet_address: str) -> Decimal:
        """Single attempt to get wallet balance (called by retry logic)."""
        session = await self._get_session()
        url = f"{self.bridge_url}/wallet/balance"

        try:
            async with session.get(url, params={"wallet": wallet_address}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if 400 <= response.status < 500:
                        raise BridgeError(
                            f"Failed to get wallet balance: {error_text}",
                            status_code=response.status,
                        )
                    raise aiohttp.ClientError(
                        f"Server error {response.status}: {error_text}"
                    )

                data = await response.json()
                return Decimal(str(data["balance"]))

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise

    async def close(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
