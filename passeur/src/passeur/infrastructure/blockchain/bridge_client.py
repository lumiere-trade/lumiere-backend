"""
Bridge server client with resilience patterns.

Communicates with Node.js bridge server for blockchain operations.
Mirrors Node.js bridge API endpoints 1:1.
"""

import asyncio
from typing import Any, Dict, Optional

import aiohttp
from shared.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    Retry,
    RetryConfig,
)

from passeur.config.settings import get_settings
from passeur.domain.exceptions import (
    BridgeConnectionException,
    BridgeTimeoutException,
)


class BridgeClient:
    """
    Client for Node.js bridge server with resilience.

    Features:
    - Circuit breaker for bridge availability
    - Retry with exponential backoff
    - Timeout protection

    All methods mirror Node.js bridge endpoints exactly.
    """

    def __init__(self, bridge_url: Optional[str] = None):
        """
        Initialize bridge client.

        Args:
            bridge_url: Optional bridge URL. If None, uses settings.
        """
        self._settings = get_settings()
        self.bridge_url = bridge_url or self._settings.bridge_url

        cb_config = self._settings.get_circuit_breaker_config("bridge_server")
        self.circuit_breaker = CircuitBreaker(
            name="bridge_server",
            config=CircuitBreakerConfig(
                failure_threshold=cb_config.failure_threshold,
                success_threshold=cb_config.success_threshold,
                timeout=cb_config.timeout,
                expected_exceptions=(
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    BridgeConnectionException,
                ),
            ),
        )

        retry_config = self._settings.get_retry_config("transaction_submission")
        self.retry = Retry(
            name="bridge_call",
            config=RetryConfig(
                max_attempts=retry_config.max_attempts,
                initial_delay=retry_config.initial_delay,
                max_delay=retry_config.max_delay,
                exponential_base=retry_config.exponential_base,
                jitter=retry_config.jitter,
                retry_on=(
                    aiohttp.ClientError,
                    BridgeConnectionException,
                ),
            ),
        )

        self.bridge_timeout = self._settings.resilience.timeouts.bridge_call

    async def _call_bridge(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Call bridge server endpoint with resilience.

        Args:
            endpoint: Endpoint path
            method: HTTP method
            data: Optional request body
            params: Optional query parameters

        Returns:
            Response data

        Raises:
            BridgeConnectionException: On connection error
            BridgeTimeoutException: On timeout
        """
        return await self.circuit_breaker.call_async(
            self._call_bridge_with_retry,
            endpoint,
            method,
            data,
            params,
        )

    async def _call_bridge_with_retry(
        self,
        endpoint: str,
        method: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Call bridge with retry logic."""
        return await self.retry.execute_async(
            self._call_bridge_inner,
            endpoint,
            method,
            data,
            params,
        )

    async def _call_bridge_inner(
        self,
        endpoint: str,
        method: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Inner bridge call implementation."""
        url = f"{self.bridge_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.bridge_timeout),
                ) as response:
                    response.raise_for_status()
                    return await response.json()

        except aiohttp.ClientError as e:
            raise BridgeConnectionException(
                f"Bridge connection error: {str(e)}",
                details={"endpoint": endpoint, "method": method},
            )
        except asyncio.TimeoutError:
            raise BridgeTimeoutException(
                f"Bridge timeout: {endpoint}",
                details={"endpoint": endpoint, "timeout": self.bridge_timeout},
            )

    async def prepare_initialize(
        self,
        user_wallet: str,
        max_balance: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepare initialize escrow transaction.

        Corresponds to: POST /escrow/prepare-initialize

        Args:
            user_wallet: User wallet public key
            max_balance: Optional max balance in lamports

        Returns:
            {
                "success": bool,
                "transaction": str,
                "escrowAccount": str,
                "bump": int,
                "message": str
            }
        """
        payload = {"userWallet": user_wallet}
        if max_balance is not None:
            payload["maxBalance"] = max_balance

        return await self._call_bridge(
            "/escrow/prepare-initialize",
            method="POST",
            data=payload,
        )

    async def prepare_delegate_platform(
        self,
        user_wallet: str,
        escrow_account: str,
        authority: str,
    ) -> Dict[str, Any]:
        """
        Prepare delegate platform authority transaction.

        Corresponds to: POST /escrow/prepare-delegate-platform

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address
            authority: Platform authority public key

        Returns:
            {
                "success": bool,
                "transaction": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-delegate-platform",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
                "authority": authority,
            },
        )

    async def prepare_delegate_trading(
        self,
        user_wallet: str,
        escrow_account: str,
        authority: str,
    ) -> Dict[str, Any]:
        """
        Prepare delegate trading authority transaction.

        Corresponds to: POST /escrow/prepare-delegate-trading

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address
            authority: Trading authority public key

        Returns:
            {
                "success": bool,
                "transaction": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-delegate-trading",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
                "authority": authority,
            },
        )

    async def prepare_revoke_platform(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> Dict[str, Any]:
        """
        Prepare revoke platform authority transaction.

        Corresponds to: POST /escrow/prepare-revoke-platform

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address

        Returns:
            {
                "success": bool,
                "transaction": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-revoke-platform",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
            },
        )

    async def prepare_revoke_trading(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> Dict[str, Any]:
        """
        Prepare revoke trading authority transaction.

        Corresponds to: POST /escrow/prepare-revoke-trading

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address

        Returns:
            {
                "success": bool,
                "transaction": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-revoke-trading",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
            },
        )

    async def prepare_deposit(
        self,
        user_wallet: str,
        escrow_account: str,
        amount: float,
    ) -> Dict[str, Any]:
        """
        Prepare deposit transaction.

        Corresponds to: POST /escrow/prepare-deposit

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address
            amount: Amount to deposit in USDC (not lamports)

        Returns:
            {
                "success": bool,
                "transaction": str,
                "amount": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-deposit",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
                "amount": amount,
            },
        )

    async def prepare_withdraw(
        self,
        user_wallet: str,
        escrow_account: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Prepare withdraw transaction.

        Corresponds to: POST /escrow/prepare-withdraw

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address
            amount: Optional amount in USDC. If None, withdraws all

        Returns:
            {
                "success": bool,
                "transaction": str,
                "amount": str,
                "message": str
            }
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
        }
        if amount is not None:
            payload["amount"] = amount

        return await self._call_bridge(
            "/escrow/prepare-withdraw",
            method="POST",
            data=payload,
        )

    async def prepare_close(
        self,
        user_wallet: str,
        escrow_account: str,
    ) -> Dict[str, Any]:
        """
        Prepare close escrow transaction.

        Corresponds to: POST /escrow/prepare-close

        Args:
            user_wallet: User wallet public key
            escrow_account: Escrow account address

        Returns:
            {
                "success": bool,
                "transaction": str,
                "message": str
            }
        """
        return await self._call_bridge(
            "/escrow/prepare-close",
            method="POST",
            data={
                "userWallet": user_wallet,
                "escrowAccount": escrow_account,
            },
        )

    async def submit_transaction(
        self,
        signed_transaction: str,
    ) -> Dict[str, Any]:
        """
        Submit signed transaction to blockchain.

        Corresponds to: POST /transaction/submit

        Args:
            signed_transaction: Base64 encoded signed transaction

        Returns:
            {
                "success": bool,
                "signature": str
            }
        """
        return await self._call_bridge(
            "/transaction/submit",
            method="POST",
            data={"signedTransaction": signed_transaction},
        )

    async def get_escrow_details(
        self,
        escrow_address: str,
    ) -> Dict[str, Any]:
        """
        Get escrow account details.

        Corresponds to: GET /escrow/{address}

        Args:
            escrow_address: Escrow account address

        Returns:
            {
                "success": bool,
                "data": {...}
            }
        """
        return await self._call_bridge(
            f"/escrow/{escrow_address}",
            method="GET",
        )

    async def get_escrow_balance(
        self,
        escrow_account: str,
    ) -> Dict[str, Any]:
        """
        Get escrow token balance.

        Corresponds to: GET /escrow/balance/{account}

        Args:
            escrow_account: Escrow account address

        Returns:
            {
                "success": bool,
                "balance": float,
                "balanceLamports": str,
                "decimals": int,
                "tokenMint": str
            }
        """
        return await self._call_bridge(
            f"/escrow/balance/{escrow_account}",
            method="GET",
        )

    async def get_transaction_status(
        self,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Get transaction confirmation status.

        Corresponds to: GET /transaction/status/{signature}

        Args:
            signature: Transaction signature

        Returns:
            {
                "success": bool,
                "confirmed": bool,
                "confirmationStatus": str,
                "slot": int,
                "err": dict
            }
        """
        return await self._call_bridge(
            f"/transaction/status/{signature}",
            method="GET",
        )

    async def get_wallet_balance(
        self,
        wallet_address: str,
    ) -> Dict[str, Any]:
        """
        Get wallet token balance.

        Corresponds to: GET /wallet/balance?wallet={address}

        Args:
            wallet_address: Wallet public key

        Returns:
            {
                "success": bool,
                "balance": float,
                "balanceLamports": str,
                "decimals": int,
                "tokenMint": str,
                "wallet": str
            }
        """
        return await self._call_bridge(
            "/wallet/balance",
            method="GET",
            params={"wallet": wallet_address},
        )
