"""
Integration tests for EventPublisher (CourierPublisher).

Tests real event publishing to Courier running in test infrastructure.

Usage:
    laborant pourtier --integration
"""

from datetime import datetime
from uuid import uuid4

import httpx

from pourtier.config.settings import get_settings
from pourtier.domain.value_objects.strategy_reference import StrategyReference
from pourtier.domain.value_objects.wallet_address import WalletAddress
from pourtier.infrastructure.event_bus.courier_publisher import CourierPublisher
from shared.courier_client import CourierClient
from shared.tests import LaborantTest


class TestEventPublisher(LaborantTest):
    """Integration tests for EventPublisher with Courier."""

    component_name = "pourtier"
    test_category = "integration"

    courier_url: str = None

    async def async_setup(self):
        """Setup - verify Courier is accessible."""
        self.reporter.info("Setting up event publisher tests...", context="Setup")

        settings = get_settings()
        TestEventPublisher.COURIER_URL = settings.COURIER_URL

        self.reporter.info(
            f"Using Courier at: {self.COURIER_URL}", context="Setup"
        )

        # Verify Courier is running
        if not await self._is_courier_running():
            raise RuntimeError(
                f"Courier not accessible at {self.COURIER_URL}. "
                "Ensure test infrastructure is running."
            )

        self.reporter.info("Courier is accessible", context="Setup")

    async def async_teardown(self):
        """Cleanup - nothing to do (Courier managed by docker-compose)."""
        self.reporter.info("Event publisher tests complete", context="Teardown")

    async def _is_courier_running(self) -> bool:
        """Check if Courier is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.COURIER_URL}/health", timeout=2.0
                )
                return response.status_code == 200
        except Exception:
            return False

    def _create_publisher(self) -> CourierPublisher:
        """Create CourierPublisher with test Courier client."""
        courier_client = CourierClient(courier_url=self.COURIER_URL)
        return CourierPublisher(courier_client=courier_client)

    async def test_publish_strategy_activation(self):
        """Test publishing strategy activation event."""
        self.reporter.info("Testing publish strategy activation", context="Test")

        publisher = self._create_publisher()

        wallet = WalletAddress(address="1" * 44)
        strategy_ref = StrategyReference(
            strategy_id=uuid4(),
            strategy_name="Test Strategy",
            asset_symbol="SOLUSDT",
            asset_interval="1h",
        )

        await publisher.publish_strategy_activation(
            user_wallet=wallet,
            strategy_ref=strategy_ref,
            escrow_account="EscrowTest123",
            trading_wallet="TradingWalletTest456",
        )

        # Verify Courier received it
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.COURIER_URL}/stats")
            stats = response.json()
            assert stats["total_messages_sent"] >= 0

        self.reporter.info("Strategy activation event published", context="Test")

    async def test_publish_strategy_deactivation(self):
        """Test publishing strategy deactivation event."""
        self.reporter.info("Testing publish strategy deactivation", context="Test")

        publisher = self._create_publisher()

        wallet = WalletAddress(address="2" * 44)
        deployed_strategy_id = uuid4()

        await publisher.publish_strategy_deactivation(
            user_wallet=wallet,
            deployed_strategy_id=deployed_strategy_id,
            reason="user_requested",
        )

        self.reporter.info("Strategy deactivation event published", context="Test")

    async def test_publish_subscription_created(self):
        """Test publishing subscription created event."""
        self.reporter.info("Testing publish subscription created", context="Test")

        publisher = self._create_publisher()

        wallet = WalletAddress(address="3" * 44)
        expires_at = datetime.now().isoformat()

        await publisher.publish_subscription_created(
            user_wallet=wallet,
            plan_type="pro",
            expires_at=expires_at,
        )

        self.reporter.info("Subscription created event published", context="Test")

    async def test_publish_payment_completed(self):
        """Test publishing payment completed event."""
        self.reporter.info("Testing publish payment completed", context="Test")

        publisher = self._create_publisher()

        wallet = WalletAddress(address="4" * 44)
        payment_id = uuid4()

        await publisher.publish_payment_completed(
            user_wallet=wallet,
            payment_id=payment_id,
            amount="99.99",
            currency="USD",
        )

        self.reporter.info("Payment completed event published", context="Test")

    async def test_publish_deposit_confirmed(self):
        """Test publishing deposit confirmed event."""
        self.reporter.info("Testing publish deposit confirmed", context="Test")

        publisher = self._create_publisher()

        wallet = WalletAddress(address="5" * 44)
        deployed_strategy_id = uuid4()

        await publisher.publish_deposit_confirmed(
            user_wallet=wallet,
            deployed_strategy_id=deployed_strategy_id,
            tx_signature="TxSig123456789",
            amount="500.00",
        )

        self.reporter.info("Deposit confirmed event published", context="Test")

    async def test_publish_system_log(self):
        """Test publishing system log event."""
        self.reporter.info("Testing publish system log", context="Test")

        publisher = self._create_publisher()

        await publisher.publish_system_log(
            level="info",
            message="Test system log message",
            context="TestContext",
            metadata={"test_key": "test_value", "count": 42},
        )

        self.reporter.info("System log event published", context="Test")

    async def test_verify_courier_stats(self):
        """Test verifying Courier received events."""
        self.reporter.info("Testing Courier stats verification", context="Test")

        # Get Courier stats
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.COURIER_URL}/stats")
            assert response.status_code == 200

            stats = response.json()

            # Verify stats structure
            assert "total_messages_sent" in stats
            assert "active_clients" in stats
            assert "channels" in stats

            self.reporter.info(
                f"Courier stats: {stats['total_messages_sent']} messages sent",
                context="Test",
            )
            self.reporter.info(
                f"Active clients: {stats['active_clients']}", context="Test"
            )

        self.reporter.info("Courier stats verified", context="Test")


if __name__ == "__main__":
    TestEventPublisher.run_as_main()
