"""
Event publisher service interface.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from pourtier.domain.value_objects.strategy_reference import StrategyReference
from pourtier.domain.value_objects.wallet_address import WalletAddress


class IEventPublisher(ABC):
    """
    Abstract service interface for publishing events to Courier.

    All inter-component communication happens through events.
    Pourtier publishes events, other components subscribe.
    """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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
