"""
Solana RPC client with resilience patterns.

Features:
- Circuit Breaker (prevent cascading failures)
- Retry with exponential backoff
- Timeout protection
- Rate limiting
"""

import asyncio
from typing import Any, Dict, Optional

import aiohttp
from shared.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    Retry,
    RetryConfig,
    with_timeout,
)

from passeur.config.settings import get_settings
from passeur.domain.exceptions import RPCException, TransactionTimeoutException


class SolanaRPCClient:
    """
    Solana RPC client with circuit breaker and retry logic.
    
    Resilience features:
    - Circuit breaker to prevent cascading failures
    - Automatic retry with exponential backoff
    - Timeout protection for all RPC calls
    - Rate limiting (via shared package)
    """

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Solana RPC client.

        Args:
            rpc_url: Optional RPC URL. If None, uses settings.
        """
        self._settings = get_settings()
        self.rpc_url = rpc_url or self._settings.solana_rpc_url
        
        # Circuit breaker config
        cb_config = self._settings.get_circuit_breaker_config("solana_rpc")
        self.circuit_breaker = CircuitBreaker(
            name="solana_rpc",
            config=CircuitBreakerConfig(
                failure_threshold=cb_config.failure_threshold,
                success_threshold=cb_config.success_threshold,
                timeout=cb_config.timeout,
                expected_exceptions=(
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    RPCException,
                ),
            ),
        )
        
        # Retry config
        retry_config = self._settings.get_retry_config("rpc_query")
        self.retry = Retry(
            name="rpc_query",
            config=RetryConfig(
                max_attempts=retry_config.max_attempts,
                initial_delay=retry_config.initial_delay,
                max_delay=retry_config.max_delay,
                exponential_base=retry_config.exponential_base,
                jitter=retry_config.jitter,
                retry_on=(
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    RPCException,
                ),
            ),
        )
        
        # Timeouts
        self.rpc_timeout = self._settings.resilience.timeouts.rpc_call

    @with_timeout(10.0)
    async def call_rpc(
        self,
        method: str,
        params: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Call Solana RPC method with resilience.

        Args:
            method: RPC method name
            params: Optional method parameters

        Returns:
            RPC response

        Raises:
            RPCException: On RPC error
            CircuitBreakerOpenError: If circuit is open
        """
        return await self.circuit_breaker.call_async(
            self._call_rpc_with_retry,
            method,
            params,
        )

    async def _call_rpc_with_retry(
        self,
        method: str,
        params: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Call RPC with retry logic."""
        return await self.retry.execute_async(
            self._call_rpc_inner,
            method,
            params,
        )

    async def _call_rpc_inner(
        self,
        method: str,
        params: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Inner RPC call implementation."""
        if not self.rpc_url:
            raise RPCException("Solana RPC URL not configured")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.rpc_timeout),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "error" in data:
                        raise RPCException(
                            f"RPC error: {data['error']}",
                            details={"method": method, "error": data["error"]},
                        )
                    
                    return data.get("result", {})
        
        except aiohttp.ClientError as e:
            raise RPCException(
                f"RPC connection error: {str(e)}",
                details={"method": method},
            )
        except asyncio.TimeoutError:
            raise RPCException(
                f"RPC timeout: {method}",
                details={"method": method, "timeout": self.rpc_timeout},
            )

    async def get_balance(self, pubkey: str) -> int:
        """
        Get account balance.

        Args:
            pubkey: Public key

        Returns:
            Balance in lamports
        """
        result = await self.call_rpc("getBalance", [pubkey])
        return result.get("value", 0)

    async def get_transaction(self, signature: str) -> Dict[str, Any]:
        """
        Get transaction details.

        Args:
            signature: Transaction signature

        Returns:
            Transaction data
        """
        return await self.call_rpc(
            "getTransaction",
            [signature, {"encoding": "json"}],
        )

    async def confirm_transaction(
        self,
        signature: str,
        timeout: float = 30.0,
    ) -> bool:
        """
        Wait for transaction confirmation.

        Args:
            signature: Transaction signature
            timeout: Confirmation timeout

        Returns:
            True if confirmed

        Raises:
            TransactionTimeoutException: If confirmation times out
        """
        deadline = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                result = await self.call_rpc(
                    "getSignatureStatuses",
                    [[signature]],
                )
                
                statuses = result.get("value", [])
                if statuses and statuses[0]:
                    status = statuses[0]
                    if status.get("confirmationStatus") == "confirmed":
                        return True
                
                await asyncio.sleep(1.0)
            
            except RPCException:
                # Continue waiting on RPC errors
                await asyncio.sleep(1.0)
        
        raise TransactionTimeoutException(
            f"Transaction confirmation timeout: {signature}",
            details={"signature": signature, "timeout": timeout},
        )
