"""
Unit tests for ShutdownManager.

Tests graceful shutdown coordination and state management.

Usage:
    laborant courier --unit
"""

import asyncio
import signal

from courier.infrastructure.shutdown import ShutdownManager
from courier.infrastructure.shutdown.shutdown_manager import ShutdownState
from shared.tests import LaborantTest


class TestShutdownManager(LaborantTest):
    """Unit tests for ShutdownManager."""

    component_name = "courier"
    test_category = "unit"

    # ================================================================
    # Initialization tests
    # ================================================================

    def test_initialization_defaults(self):
        """Test ShutdownManager initializes with correct defaults."""
        self.reporter.info("Testing initialization defaults", context="Test")

        manager = ShutdownManager(shutdown_timeout=30, grace_period=5)

        assert manager.state == ShutdownState.RUNNING
        assert manager.shutdown_timeout == 30
        assert manager.grace_period == 5
        assert manager.shutdown_started_at is None
        assert manager.is_running() is True
        assert manager.is_shutting_down() is False

        self.reporter.info("Initialization defaults correct", context="Test")

    def test_initialization_custom_values(self):
        """Test ShutdownManager initializes with custom values."""
        self.reporter.info("Testing custom initialization", context="Test")

        manager = ShutdownManager(shutdown_timeout=60, grace_period=10)

        assert manager.shutdown_timeout == 60
        assert manager.grace_period == 10

        self.reporter.info("Custom initialization works", context="Test")

    # ================================================================
    # State management tests
    # ================================================================

    def test_is_running_initial_state(self):
        """Test is_running returns True initially."""
        self.reporter.info("Testing initial running state", context="Test")

        manager = ShutdownManager()

        assert manager.is_running() is True
        assert manager.state == ShutdownState.RUNNING

        self.reporter.info("Initial state correct", context="Test")

    def test_is_shutting_down_initial_state(self):
        """Test is_shutting_down returns False initially."""
        self.reporter.info("Testing initial shutdown state", context="Test")

        manager = ShutdownManager()

        assert manager.is_shutting_down() is False

        self.reporter.info("Not shutting down initially", context="Test")

    async def test_initiate_shutdown_changes_state(self):
        """Test initiate_shutdown changes state correctly."""
        self.reporter.info("Testing shutdown state change", context="Test")

        manager = ShutdownManager()

        await manager.initiate_shutdown("test")

        assert manager.state == ShutdownState.SHUTTING_DOWN
        assert manager.is_running() is False
        assert manager.is_shutting_down() is True
        assert manager.shutdown_started_at is not None

        self.reporter.info("Shutdown state changed correctly", context="Test")

    async def test_initiate_shutdown_sets_event(self):
        """Test initiate_shutdown sets shutdown event."""
        self.reporter.info("Testing shutdown event set", context="Test")

        manager = ShutdownManager()

        # Start waiting for shutdown in background
        wait_task = asyncio.create_task(manager.wait_for_shutdown())

        # Give task time to start waiting
        await asyncio.sleep(0.1)

        # Initiate shutdown
        await manager.initiate_shutdown("test")

        # Wait task should complete immediately
        await asyncio.wait_for(wait_task, timeout=1.0)

        self.reporter.info("Shutdown event set correctly", context="Test")

    async def test_initiate_shutdown_idempotent(self):
        """Test initiate_shutdown is idempotent."""
        self.reporter.info("Testing shutdown idempotency", context="Test")

        manager = ShutdownManager()

        await manager.initiate_shutdown("first")
        first_timestamp = manager.shutdown_started_at

        await asyncio.sleep(0.01)

        await manager.initiate_shutdown("second")
        second_timestamp = manager.shutdown_started_at

        # Timestamp should not change on second call
        assert first_timestamp == second_timestamp
        assert manager.state == ShutdownState.SHUTTING_DOWN

        self.reporter.info("Shutdown idempotent", context="Test")

    def test_mark_shutdown_complete(self):
        """Test mark_shutdown_complete changes state."""
        self.reporter.info("Testing mark shutdown complete", context="Test")

        manager = ShutdownManager()

        manager.mark_shutdown_complete()

        assert manager.state == ShutdownState.SHUTDOWN
        assert manager.is_shutting_down() is True

        self.reporter.info("Shutdown marked complete", context="Test")

    # ================================================================
    # Callback registration tests
    # ================================================================

    async def test_register_shutdown_callback_called(self):
        """Test registered callbacks are called on shutdown."""
        self.reporter.info("Testing callback execution", context="Test")

        manager = ShutdownManager()
        callback_called = False

        async def callback():
            nonlocal callback_called
            callback_called = True

        manager.register_shutdown_callback(callback)

        await manager.initiate_shutdown("test")

        assert callback_called is True

        self.reporter.info("Callback executed", context="Test")

    async def test_register_multiple_callbacks_execution_order(self):
        """Test multiple callbacks executed in registration order."""
        self.reporter.info("Testing multiple callbacks", context="Test")

        manager = ShutdownManager()
        call_order = []

        async def callback1():
            call_order.append(1)

        async def callback2():
            call_order.append(2)

        async def callback3():
            call_order.append(3)

        manager.register_shutdown_callback(callback1)
        manager.register_shutdown_callback(callback2)
        manager.register_shutdown_callback(callback3)

        await manager.initiate_shutdown("test")

        assert call_order == [1, 2, 3]

        self.reporter.info("Callbacks executed in order", context="Test")

    async def test_callback_exception_does_not_stop_shutdown(self):
        """Test callback exception doesn't prevent shutdown."""
        self.reporter.info("Testing callback exception handling", context="Test")

        manager = ShutdownManager()
        callback2_called = False

        async def failing_callback():
            raise RuntimeError("Test error")

        async def callback2():
            nonlocal callback2_called
            callback2_called = True

        manager.register_shutdown_callback(failing_callback)
        manager.register_shutdown_callback(callback2)

        await manager.initiate_shutdown("test")

        # Shutdown should proceed despite exception
        assert manager.is_shutting_down() is True
        assert callback2_called is True

        self.reporter.info("Exception handled gracefully", context="Test")

    async def test_sync_callback_works(self):
        """Test synchronous callbacks work."""
        self.reporter.info("Testing sync callback", context="Test")

        manager = ShutdownManager()
        callback_called = False

        def sync_callback():
            nonlocal callback_called
            callback_called = True

        manager.register_shutdown_callback(sync_callback)

        await manager.initiate_shutdown("test")

        assert callback_called is True

        self.reporter.info("Sync callback worked", context="Test")

    # ================================================================
    # Signal handler tests
    # ================================================================

    def test_setup_signal_handlers_registers_handlers(self):
        """Test setup_signal_handlers registers handlers."""
        self.reporter.info("Testing signal handler registration", context="Test")

        manager = ShutdownManager()

        original_sigterm = signal.getsignal(signal.SIGTERM)
        original_sigint = signal.getsignal(signal.SIGINT)

        manager.setup_signal_handlers()

        new_sigterm = signal.getsignal(signal.SIGTERM)
        new_sigint = signal.getsignal(signal.SIGINT)

        # Handlers should be changed
        assert new_sigterm != original_sigterm
        assert new_sigint != original_sigint

        # Cleanup
        manager.restore_signal_handlers()

        self.reporter.info("Signal handlers registered", context="Test")

    def test_restore_signal_handlers_restores_originals(self):
        """Test restore_signal_handlers restores original handlers."""
        self.reporter.info("Testing signal handler restoration", context="Test")

        manager = ShutdownManager()

        original_sigterm = signal.getsignal(signal.SIGTERM)
        original_sigint = signal.getsignal(signal.SIGINT)

        manager.setup_signal_handlers()
        manager.restore_signal_handlers()

        restored_sigterm = signal.getsignal(signal.SIGTERM)
        restored_sigint = signal.getsignal(signal.SIGINT)

        assert restored_sigterm == original_sigterm
        assert restored_sigint == original_sigint

        self.reporter.info("Signal handlers restored", context="Test")

    # ================================================================
    # Shutdown info tests
    # ================================================================

    def test_get_shutdown_info_initial_state(self):
        """Test get_shutdown_info returns correct initial state."""
        self.reporter.info("Testing shutdown info initial", context="Test")

        manager = ShutdownManager(shutdown_timeout=30, grace_period=5)

        info = manager.get_shutdown_info()

        assert info["state"] == "running"
        assert info["is_shutting_down"] is False
        assert info["shutdown_started_at"] is None
        assert info["shutdown_timeout"] == 30
        assert info["grace_period"] == 5

        self.reporter.info("Shutdown info correct", context="Test")

    async def test_get_shutdown_info_during_shutdown(self):
        """Test get_shutdown_info returns correct state during shutdown."""
        self.reporter.info("Testing shutdown info during shutdown", context="Test")

        manager = ShutdownManager()

        await manager.initiate_shutdown("test")

        info = manager.get_shutdown_info()

        assert info["state"] == "shutting_down"
        assert info["is_shutting_down"] is True
        assert info["shutdown_started_at"] is not None
        assert isinstance(info["shutdown_started_at"], str)

        self.reporter.info("Shutdown info correct during shutdown", context="Test")

    # ================================================================
    # Wait for shutdown tests
    # ================================================================

    async def test_wait_for_shutdown_blocks_until_initiated(self):
        """Test wait_for_shutdown blocks until shutdown initiated."""
        self.reporter.info("Testing wait for shutdown blocking", context="Test")

        manager = ShutdownManager()
        wait_completed = False

        async def waiter():
            nonlocal wait_completed
            await manager.wait_for_shutdown()
            wait_completed = True

        wait_task = asyncio.create_task(waiter())

        # Give task time to start waiting
        await asyncio.sleep(0.1)

        # Should not have completed yet
        assert wait_completed is False

        # Initiate shutdown
        await manager.initiate_shutdown("test")

        # Wait should complete
        await asyncio.wait_for(wait_task, timeout=1.0)
        assert wait_completed is True

        self.reporter.info("Wait blocked correctly", context="Test")

    async def test_wait_for_shutdown_complete_with_timeout(self):
        """Test wait_for_shutdown_complete with timeout."""
        self.reporter.info("Testing wait for shutdown with timeout", context="Test")

        manager = ShutdownManager()

        # Start waiting (shutdown not initiated)
        result = await manager.wait_for_shutdown_complete(timeout=0.1)

        # Should timeout
        assert result is False

        self.reporter.info("Timeout worked correctly", context="Test")

    async def test_wait_for_shutdown_complete_success(self):
        """Test wait_for_shutdown_complete succeeds when shutdown initiated."""
        self.reporter.info("Testing wait for shutdown success", context="Test")

        manager = ShutdownManager()

        # Initiate shutdown first
        await manager.initiate_shutdown("test")

        # Wait should succeed immediately
        result = await manager.wait_for_shutdown_complete(timeout=1.0)

        assert result is True

        self.reporter.info("Wait succeeded", context="Test")


if __name__ == "__main__":
    TestShutdownManager.run_as_main()
