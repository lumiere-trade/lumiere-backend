"""
Courier event publisher adapter.

Publishes events to Courier channels for inter-component communication.
"""

from typing import Any
from uuid import UUID

from pourtier.domain.services.i_event_publisher import IEventPublisher
from pourtier.domain.value_objects.strategy_reference import StrategyReference
from pourtier.domain.value_objects.wallet_address import WalletAddress
from shared.courier_client import CourierClient


class CourierPublisher(IEventPublisher):
    """
    Courier-based event publisher.

    Publishes domain events to Courier channels.
    """

    def __init__(self, courier_client: CourierClient):
        """
        Initialize publisher with Courier client.

        Args:
            courier_client: Shared Courier client instance
        """
        self.courier = courier_client

    async def publish_strategy_activation(
        self,
        user_wallet: WalletAddress,
        strategy_ref: StrategyReference,
        escrow_account: str,
        trading_wallet: str,
    ) -> None:
        """
        Publish strategy activation event.

        Args:
            user_wallet: User's wallet address
            strategy_ref: Strategy reference details
            escrow_account: Escrow PDA address
            trading_wallet: Trading wallet address
        """
        event = {
            "event": "strategy.activation_requested",
            "user_wallet": user_wallet.address,
            "strategy_id": str(strategy_ref.strategy_id),
            "strategy_name": strategy_ref.strategy_name,
            "asset_symbol": strategy_ref.asset_symbol,
            "asset_interval": strategy_ref.asset_interval,
            "escrow_account": escrow_account,
            "trading_wallet": trading_wallet,
        }

        await self.courier.publish("strategy", event)

    async def publish_strategy_deactivation(
        self, user_wallet: WalletAddress, deployed_strategy_id: UUID, reason: str
    ) -> None:
        """
        Publish strategy deactivation event.

        Args:
            user_wallet: User's wallet address
            deployed_strategy_id: Deployed strategy ID
            reason: Reason for deactivation
        """
        event = {
            "event": "strategy.deactivation_requested",
            "user_wallet": user_wallet.address,
            "deployed_strategy_id": str(deployed_strategy_id),
            "reason": reason,
        }

        await self.courier.publish("strategy", event)

    async def publish_subscription_created(
        self, user_wallet: WalletAddress, plan_type: str, expires_at: str
    ) -> None:
        """
        Publish subscription created event.

        Args:
            user_wallet: User's wallet address
            plan_type: Subscription plan type
            expires_at: Expiration timestamp ISO format
        """
        event = {
            "event": "subscription.created",
            "user_wallet": user_wallet.address,
            "plan_type": plan_type,
            "expires_at": expires_at,
        }

        await self.courier.publish("subscription", event)

    async def publish_payment_completed(
        self, user_wallet: WalletAddress, payment_id: UUID, amount: str, currency: str
    ) -> None:
        """
        Publish payment completed event.

        Args:
            user_wallet: User's wallet address
            payment_id: Payment entity ID
            amount: Payment amount
            currency: Currency code
        """
        event = {
            "event": "payment.completed",
            "user_wallet": user_wallet.address,
            "payment_id": str(payment_id),
            "amount": amount,
            "currency": currency,
        }

        await self.courier.publish("payment", event)

    async def publish_deposit_confirmed(
        self,
        user_wallet: WalletAddress,
        deployed_strategy_id: UUID,
        tx_signature: str,
        amount: str,
    ) -> None:
        """
        Publish deposit confirmed event.

        Args:
            user_wallet: User's wallet address
            deployed_strategy_id: Deployed strategy ID
            tx_signature: Solana transaction signature
            amount: Deposit amount
        """
        event = {
            "event": "deposit.confirmed",
            "user_wallet": user_wallet.address,
            "deployed_strategy_id": str(deployed_strategy_id),
            "tx_signature": tx_signature,
            "amount": amount,
        }

        await self.courier.publish("deposit", event)

    async def publish_system_log(
        self,
        level: str,
        message: str,
        context: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Publish system log message to Courier sys channel.

        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            context: Component context
            metadata: Optional additional data
        """
        event = {
            "type": "system_log",
            "level": level,
            "message": message,
            "context": context,
            "metadata": metadata or {},
        }

        await self.courier.publish("sys", event)
