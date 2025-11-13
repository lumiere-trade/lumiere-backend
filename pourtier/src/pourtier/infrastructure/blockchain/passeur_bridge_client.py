"""
Passeur Bridge client implementation.

HTTP client for communicating with Passeur Bridge API.
Production-hardened with Circuit Breaker, Retry, and Metrics.
"""

import asyncio
from decimal import Decimal
from typing import Optional

import aiohttp
from prometheus_client import Counter, Histogram

from pourtier.domain.exceptions.blockchain import BridgeError
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from shared.resilience import (
    BackoffStrategy,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    Retry,
    RetryConfig,
)

# Prometheus Metrics
passeur_requests_total = Counter(
    "passeur_requests_total",
    "Total Passeur Bridge requests",
    ["operation", "status"],
)

passeur_request_duration = Histogram(
    "passeur_request_duration_seconds",
    "Passeur Bridge request duration",
    ["operation"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

passeur_circuit_breaker_state = Counter(
    "passeur_circuit_breaker_state_changes_total",
    "Passeur Circuit Breaker state changes",
    ["state"],
)


class PasseurBridgeClient(IPasseurBridge):
    """
    Passeur Bridge HTTP client.

    Production-hardened with:
    - Circuit Breaker (prevents cascading failures)
    - Exponential Retry with Jitter (handles transient errors)
    - Prometheus Metrics (observability)
    - Optimized Timeouts (balanced for performance)
    """

    def __init__(
        self,
        bridge_url: str,
        total_timeout: float = 30.0,
        connect_timeout: float = 10.0,
        max_retries: int = 3,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize Passeur Bridge client.

        Args:
            bridge_url: Passeur Bridge API base URL
            total_timeout: Total request timeout (default: 30s)
            connect_timeout: Connection timeout (default: 10s)
            max_retries: Max retry attempts (default: 3)
            circuit_breaker_config: Optional Circuit Breaker config
        """
        self.bridge_url = bridge_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(
            total=total_timeout,
            connect=connect_timeout,
        )
        self._session: Optional[aiohttp.ClientSession] = None

        # Circuit Breaker for Passeur calls
        cb_config = circuit_breaker_config or CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout=60.0,
            expected_exceptions=(
                aiohttp.ClientError,
                asyncio.TimeoutError,
                BridgeError,
            ),
        )
        self.circuit_breaker = CircuitBreaker("passeur_bridge", cb_config)

        # Retry with exponential backoff + jitter
        self.retry_config = RetryConfig(
            max_attempts=max_retries,
            initial_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            jitter=True,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            retry_on=(aiohttp.ClientError, asyncio.TimeoutError),
        )
        self.retry = Retry(self.retry_config)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with optimized settings."""
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

    async def _make_request_with_resilience(
        self,
        endpoint: str,
        payload: dict,
        operation: str,
    ) -> str:
        """
        Make HTTP request with Circuit Breaker + Retry.

        Args:
            endpoint: API endpoint path
            payload: Request JSON payload
            operation: Operation name for metrics

        Returns:
            Transaction string from response

        Raises:
            BridgeError: If request fails after all retries
            CircuitBreakerOpenError: If circuit is open
        """
        try:
            result = await self.circuit_breaker.call_async(
                self._make_request_with_retry,
                endpoint,
                payload,
                operation,
            )
            passeur_requests_total.labels(operation=operation, status="success").inc()
            return result

        except CircuitBreakerOpenError:
            passeur_requests_total.labels(
                operation=operation, status="circuit_open"
            ).inc()
            passeur_circuit_breaker_state.labels(state="open").inc()
            raise BridgeError(f"Passeur Bridge circuit breaker is OPEN for {operation}")

        except Exception:
            passeur_requests_total.labels(operation=operation, status="error").inc()
            raise

    async def _make_request_with_retry(
        self,
        endpoint: str,
        payload: dict,
        operation: str,
    ) -> str:
        """Make HTTP request with retry logic (called by circuit breaker)."""
        with passeur_request_duration.labels(operation=operation).time():
            return await self.retry.execute_async(
                self._make_request_once,
                endpoint,
                payload,
                operation,
            )

    async def _make_request_once(
        self,
        endpoint: str,
        payload: dict,
        operation: str,
    ) -> str:
        """
        Single HTTP request attempt.

        Args:
            endpoint: API endpoint path
            payload: Request JSON payload
            operation: Operation name for error messages

        Returns:
            Transaction string from response

        Raises:
            BridgeError: If request fails (4xx errors)
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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "tokenMint": token_mint,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-initialize",
            payload=payload,
            operation="initialize_escrow",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "signedTransaction": signed_transaction,
        }

        try:
            with passeur_request_duration.labels(operation="submit_transaction").time():
                result = await self.circuit_breaker.call_async(
                    self.retry.execute_async,
                    self._submit_transaction_once,
                    payload,
                )
                passeur_requests_total.labels(
                    operation="submit_transaction", status="success"
                ).inc()
                return result

        except CircuitBreakerOpenError:
            passeur_requests_total.labels(
                operation="submit_transaction", status="circuit_open"
            ).inc()
            passeur_circuit_breaker_state.labels(state="open").inc()
            raise BridgeError(
                "Passeur Bridge circuit breaker is OPEN for " "transaction submission"
            )

        except Exception:
            passeur_requests_total.labels(
                operation="submit_transaction", status="error"
            ).inc()
            raise

    async def _submit_transaction_once(self, payload: dict) -> str:
        """Submit transaction - single attempt."""
        session = await self._get_session()
        url = f"{self.bridge_url}/transaction/submit"

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if 400 <= response.status < 500:
                        raise BridgeError(
                            f"Failed to submit transaction: {error_text}",
                            status_code=response.status,
                        )
                    raise aiohttp.ClientError(
                        f"Server error {response.status}: {error_text}"
                    )

                data = await response.json()
                return data["signature"]

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "amount": float(amount),
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-deposit",
            payload=payload,
            operation="prepare_deposit",
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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "amount": float(amount),
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-withdraw",
            payload=payload,
            operation="prepare_withdraw",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "platformAuthority": platform_authority,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-delegate-platform",
            payload=payload,
            operation="prepare_delegate_platform",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
            "tradingAuthority": trading_authority,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-delegate-trading",
            payload=payload,
            operation="prepare_delegate_trading",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-revoke-platform",
            payload=payload,
            operation="prepare_revoke_platform",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-revoke-trading",
            payload=payload,
            operation="prepare_revoke_trading",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        payload = {
            "userWallet": user_wallet,
            "escrowAccount": escrow_account,
        }

        return await self._make_request_with_resilience(
            endpoint="/escrow/prepare-close",
            payload=payload,
            operation="prepare_close",
        )

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
            CircuitBreakerOpenError: If circuit is open
        """
        try:
            with passeur_request_duration.labels(operation="get_escrow_balance").time():
                result = await self.circuit_breaker.call_async(
                    self.retry.execute_async,
                    self._get_escrow_balance_once,
                    escrow_account,
                )
                passeur_requests_total.labels(
                    operation="get_escrow_balance", status="success"
                ).inc()
                return result

        except CircuitBreakerOpenError:
            passeur_requests_total.labels(
                operation="get_escrow_balance", status="circuit_open"
            ).inc()
            passeur_circuit_breaker_state.labels(state="open").inc()
            raise BridgeError(
                "Passeur Bridge circuit breaker is OPEN for " "escrow balance query"
            )

        except Exception:
            passeur_requests_total.labels(
                operation="get_escrow_balance", status="error"
            ).inc()
            raise

    async def _get_escrow_balance_once(self, escrow_account: str) -> Decimal:
        """Single attempt to get escrow balance."""
        session = await self._get_session()
        url = f"{self.bridge_url}/escrow/balance/{escrow_account}"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if 400 <= response.status < 500:
                        raise BridgeError(
                            f"Failed to get escrow balance: {error_text}",
                            status_code=response.status,
                        )
                    raise aiohttp.ClientError(
                        f"Server error {response.status}: {error_text}"
                    )

                data = await response.json()
                return Decimal(str(data["balance"]))

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise

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
            CircuitBreakerOpenError: If circuit is open
        """
        try:
            with passeur_request_duration.labels(operation="get_escrow_details").time():
                result = await self.circuit_breaker.call_async(
                    self.retry.execute_async,
                    self._get_escrow_details_once,
                    escrow_account,
                )
                passeur_requests_total.labels(
                    operation="get_escrow_details", status="success"
                ).inc()
                return result

        except CircuitBreakerOpenError:
            passeur_requests_total.labels(
                operation="get_escrow_details", status="circuit_open"
            ).inc()
            passeur_circuit_breaker_state.labels(state="open").inc()
            raise BridgeError(
                "Passeur Bridge circuit breaker is OPEN for " "escrow details query"
            )

        except Exception:
            passeur_requests_total.labels(
                operation="get_escrow_details", status="error"
            ).inc()
            raise

    async def _get_escrow_details_once(self, escrow_account: str) -> dict:
        """Single attempt to get escrow details."""
        session = await self._get_session()
        url = f"{self.bridge_url}/escrow/{escrow_account}"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if 400 <= response.status < 500:
                        raise BridgeError(
                            f"Failed to get escrow details: {error_text}",
                            status_code=response.status,
                        )
                    raise aiohttp.ClientError(
                        f"Server error {response.status}: {error_text}"
                    )

                return await response.json()

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise

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
            CircuitBreakerOpenError: If circuit is open
        """
        try:
            with passeur_request_duration.labels(operation="get_wallet_balance").time():
                result = await self.circuit_breaker.call_async(
                    self.retry.execute_async,
                    self._get_wallet_balance_once,
                    wallet_address,
                )
                passeur_requests_total.labels(
                    operation="get_wallet_balance", status="success"
                ).inc()
                return result

        except CircuitBreakerOpenError:
            passeur_requests_total.labels(
                operation="get_wallet_balance", status="circuit_open"
            ).inc()
            passeur_circuit_breaker_state.labels(state="open").inc()
            raise BridgeError(
                "Passeur Bridge circuit breaker is OPEN for " "wallet balance query"
            )

        except Exception:
            passeur_requests_total.labels(
                operation="get_wallet_balance", status="error"
            ).inc()
            raise

    async def _get_wallet_balance_once(self, wallet_address: str) -> Decimal:
        """Single attempt to get wallet balance."""
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
