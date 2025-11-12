"""
Transaction manager with idempotency guarantees.

Ensures exactly-once execution for financial operations.
"""

from typing import Any, Dict

from shared.resilience import IdempotencyKey

from passeur.infrastructure.blockchain.bridge_client import BridgeClient
from passeur.infrastructure.blockchain.solana_rpc_client import SolanaRPCClient
from passeur.infrastructure.cache.redis_idempotency_store import (
    RedisIdempotencyStore,
)


class TransactionManager:
    """
    Manages blockchain transactions with idempotency.

    CRITICAL: All financial operations MUST use this manager to prevent:
    - Double withdrawals
    - Duplicate deposits
    - Repeated authority delegations
    """

    def __init__(
        self,
        bridge_client: BridgeClient,
        rpc_client: SolanaRPCClient,
        idempotency_store: RedisIdempotencyStore,
    ):
        """
        Initialize transaction manager.

        Args:
            bridge_client: Bridge client
            rpc_client: RPC client
            idempotency_store: Idempotency store
        """
        self.bridge = bridge_client
        self.rpc = rpc_client
        self.store = idempotency_store

    async def withdraw_from_escrow(
        self,
        escrow_account: str,
        amount: int,
        strategy_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Withdraw from escrow with idempotency.

        CRITICAL: This is a financial operation - idempotency key prevents
        double withdrawal even if called multiple times.

        Args:
            escrow_account: Escrow account public key
            amount: Amount in lamports
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            Transaction signature and details
        """
        # Generate idempotency key (deterministic from inputs)
        idempotency_key = IdempotencyKey.from_user_request(
            user_id=user_id,
            operation="withdraw",
            amount=amount,
            escrow_account=escrow_account,
            strategy_id=strategy_id,
        )

        # Check if already executed
        if await self.store.exists_async(idempotency_key):
            cached_result = await self.store.get_async(idempotency_key)
            return cached_result

        # Execute withdrawal
        result = await self.bridge.withdraw_from_escrow(
            escrow_account=escrow_account,
            amount=amount,
            strategy_id=strategy_id,
        )

        # Store result (7 days TTL for financial operations)
        await self.store.set_async(
            idempotency_key,
            result,
            ttl=7 * 24 * 60 * 60,  # 7 days
        )

        return result

    async def deposit_to_escrow(
        self,
        escrow_account: str,
        amount: int,
        user_signature: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Deposit to escrow with idempotency.

        CRITICAL: Financial operation with exactly-once semantics.

        Args:
            escrow_account: Escrow account public key
            amount: Amount in lamports
            user_signature: User's transaction signature
            user_id: User ID

        Returns:
            Transaction signature and details
        """
        # Generate idempotency key
        idempotency_key = IdempotencyKey.from_user_request(
            user_id=user_id,
            operation="deposit",
            amount=amount,
            escrow_account=escrow_account,
            user_signature=user_signature,
        )

        # Check if already executed
        if await self.store.exists_async(idempotency_key):
            cached_result = await self.store.get_async(idempotency_key)
            return cached_result

        # Execute deposit
        result = await self.bridge.deposit_to_escrow(
            escrow_account=escrow_account,
            amount=amount,
            user_signature=user_signature,
        )

        # Store result (7 days TTL)
        await self.store.set_async(
            idempotency_key,
            result,
            ttl=7 * 24 * 60 * 60,
        )

        return result

    async def initialize_escrow(
        self,
        user_pubkey: str,
        subscription_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Initialize escrow with idempotency.

        One-time operation - idempotency prevents duplicate escrow accounts.

        Args:
            user_pubkey: User public key
            subscription_id: Subscription ID
            user_id: User ID

        Returns:
            Escrow account and transaction signature
        """
        # Generate idempotency key
        idempotency_key = IdempotencyKey.from_user_request(
            user_id=user_id,
            operation="initialize_escrow",
            user_pubkey=user_pubkey,
            subscription_id=subscription_id,
        )

        # Check if already executed
        if await self.store.exists_async(idempotency_key):
            cached_result = await self.store.get_async(idempotency_key)
            return cached_result

        # Execute initialization
        result = await self.bridge.initialize_escrow(
            user_pubkey=user_pubkey,
            subscription_id=subscription_id,
        )

        # Store result (3 days TTL for security operations)
        await self.store.set_async(
            idempotency_key,
            result,
            ttl=3 * 24 * 60 * 60,
        )

        return result
