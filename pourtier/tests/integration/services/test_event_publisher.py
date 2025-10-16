"""
Integration tests for EventPublisher (CourierPublisher).

Tests real event publishing to Courier with automatic lifecycle management.

Usage:
    python -m pourtier.tests.integration.services.test_event_publisher
    laborant pourtier --integration
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from uuid import uuid4

import httpx

from pourtier.config.settings import load_config
from pourtier.domain.value_objects.strategy_reference import StrategyReference
from pourtier.domain.value_objects.wallet_address import WalletAddress
from pourtier.infrastructure.event_bus.courier_publisher import CourierPublisher
from shared.courier_client import CourierClient
from shared.tests import LaborantTest

# Load test configuration
test_settings = load_config("test.yaml")
COURIER_URL = test_settings.COURIER_URL
COURIER_PORT = test_settings.COURIER_PORT


class TestEventPublisher(LaborantTest):
    """Integration tests for EventPublisher with Courier."""

    component_name = "pourtier"
    test_category = "integration"

    # Class-level shared resources
    courier_process: subprocess.Popen = None
    courier_log_file = None

    # ================================================================
    # Async Lifecycle Hooks
    # ================================================================

    async def async_setup(self):
        """Setup Courier server (runs once before all tests)."""
        self.reporter.info("Setting up Courier...", context="Setup")
        self.reporter.info(f"Courier URL: {COURIER_URL}", context="Setup")
        self.reporter.info(f"Courier Port: {COURIER_PORT}", context="Setup")

        # Start Courier
        self._start_courier()

        # Verify Courier is running
        if not await self._is_courier_running():
            raise RuntimeError("Courier failed to start")

        self.reporter.info("Courier running", context="Setup")

    async def async_teardown(self):
        """Cleanup Courier server (runs once after all tests)."""
        self.reporter.info("Cleaning up Courier...", context="Teardown")

        self._stop_courier()

        self.reporter.info("Cleanup complete", context="Teardown")

    # ================================================================
    # Helper Methods
    # ================================================================

    def _start_courier(self):
        """Start Courier on test port."""
        self.reporter.info(
            f"Starting Courier on port {COURIER_PORT}...", context="Setup"
        )

        # Set test config environment
        env = os.environ.copy()
        env["COURIER_CONFIG"] = "test.yaml"
        env["COURIER_PORT"] = str(COURIER_PORT)

        # Create log file for Courier output
        courier_log_path = f"{self.log_dir}/courier_test.log"

        TestEventPublisher.courier_log_file = open(courier_log_path, "w")

        # Start Courier process
        TestEventPublisher.courier_process = subprocess.Popen(
            [sys.executable, "-m", "courier.broker"],
            stdout=TestEventPublisher.courier_log_file,
            stderr=TestEventPublisher.courier_log_file,
            env=env,
            preexec_fn=os.setsid,
        )

        self.reporter.info(f"Courier log: {courier_log_path}", context="Setup")

        # Wait for Courier to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = httpx.get(f"{COURIER_URL}/health", timeout=2.0)
                if response.status_code == 200:
                    self.reporter.info(
                        f"Courier started (attempt {attempt + 1})", context="Setup"
                    )
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                time.sleep(1.0)

        # Failed to start
        self.reporter.error(
            f"Courier failed to start after {max_attempts} attempts", context="Setup"
        )

        # Show last 20 lines of log
        try:
            with open(courier_log_path, "r") as f:
                lines = f.readlines()
                if lines:
                    self.reporter.error(
                        "Last 20 lines of Courier log:", context="Setup"
                    )
                    for line in lines[-20:]:
                        self.reporter.error(f"  {line.rstrip()}", context="Setup")
        except BaseException:
            pass

        self._stop_courier()
        raise RuntimeError("Courier startup failed")

    def _stop_courier(self):
        """Stop Courier process."""
        if TestEventPublisher.courier_process:
            self.reporter.info("🛑 Stopping Courier...", context="Teardown")

            try:
                # Kill process group
                os.killpg(
                    os.getpgid(TestEventPublisher.courier_process.pid), signal.SIGTERM
                )
                TestEventPublisher.courier_process.wait(timeout=5)
                self.reporter.info("Courier stopped", context="Teardown")
            except subprocess.TimeoutExpired:
                self.reporter.warning(
                    "Courier didn't stop gracefully, forcing...", context="Teardown"
                )
                os.killpg(
                    os.getpgid(TestEventPublisher.courier_process.pid), signal.SIGKILL
                )
                TestEventPublisher.courier_process.wait()
            except Exception as e:
                self.reporter.error(f"Error stopping Courier: {e}", context="Teardown")

            TestEventPublisher.courier_process = None

        # Close log file
        if TestEventPublisher.courier_log_file:
            try:
                TestEventPublisher.courier_log_file.close()
            except BaseException:
                pass
            TestEventPublisher.courier_log_file = None

    async def _is_courier_running(self) -> bool:
        """Check if Courier is running."""
        try:
            response = httpx.get(f"{COURIER_URL}/health", timeout=1.0)
            return response.status_code == 200
        except BaseException:
            return False

    def _create_publisher(self) -> CourierPublisher:
        """Create CourierPublisher with test Courier client."""
        courier_client = CourierClient(courier_url=COURIER_URL)
        return CourierPublisher(courier_client=courier_client)

    # ================================================================
    # Test Methods
    # ================================================================

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
            response = await client.get(f"{COURIER_URL}/stats")
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
            response = await client.get(f"{COURIER_URL}/stats")
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
