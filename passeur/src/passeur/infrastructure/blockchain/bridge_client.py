"""
Bridge server client with resilience patterns.

Communicates with Node.js bridge server for blockchain operations.
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
    """

    def __init__(self, bridge_url: Optional[str] = None):
        """
        Initialize bridge client.

        Args:
            bridge_url: Optional bridge URL. If None, uses settings.
        """
        self._settings = get_settings()
        self.bridge_url = bridge_url or f"http://localhost:{self._settings.bridge_port}"
        
        # Circuit breaker config
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
        
        # Retry config
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

    async def call_bridge(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call bridge server endpoint with resilience.

        Args:
            endpoint: Endpoint path (e.g., "/escrow/initialize")
            method: HTTP method
            data: Optional request data

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
        )

    async def _call_bridge_with_retry(
        self,
        endpoint: str,
        method: str,
        data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Call bridge with retry logic."""
        return await self.retry.execute_async(
            self._call_bridge_inner,
            endpoint,
            method,
            data,
        )

    async def _call_bridge_inner(
        self,
        endpoint: str,
        method: str,
        data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Inner bridge call implementation."""
        url = f"{self.bridge_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=data,
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

    async def initialize_escrow(
        self,
        user_pubkey: str,
        subscription_id: str,
    ) -> Dict[str, Any]:
        """
        Initialize escrow account.

        Args:
            user_pubkey: User public key
            subscription_id: Subscription ID

        Returns:
            Transaction signature and escrow account
        """
        return await self.call_bridge(
            "/escrow/initialize",
            method="POST",
            data={
                "userPubkey": user_pubkey,
                "subscriptionId": subscription_id,
            },
        )

    async def deposit_to_escrow(
        self,
        escrow_account: str,
        amount: int,
        user_signature: str,
    ) -> Dict[str, Any]:
        """
        Deposit to escrow.

        Args:
            escrow_account: Escrow account public key
            amount: Amount in lamports
            user_signature: User's transaction signature

        Returns:
            Transaction signature
        """
        return await self.call_bridge(
            "/escrow/deposit",
            method="POST",
            data={
                "escrowAccount": escrow_account,
                "amount": amount,
                "userSignature": user_signature,
            },
        )

    async def withdraw_from_escrow(
        self,
        escrow_account: str,
        amount: int,
        strategy_id: str,
    ) -> Dict[str, Any]:
        """
        Withdraw from escrow (platform authority).

        Args:
            escrow_account: Escrow account public key
            amount: Amount in lamports
            strategy_id: Strategy ID for audit trail

        Returns:
            Transaction signature
        """
        return await self.call_bridge(
            "/escrow/withdraw",
            method="POST",
            data={
                "escrowAccount": escrow_account,
                "amount": amount,
                "strategyId": strategy_id,
            },
        )
