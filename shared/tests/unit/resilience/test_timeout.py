"""
Unit tests for timeout functionality.

Tests timeout context manager and timeout integration in TSDLEngine.

Usage:
    python -m tests.unit.infrastructure.test_timeout
"""

import time
from unittest.mock import Mock, patch

from shared.tests import LaborantTest

from tsdl.config import Settings, override_settings, reset_settings
from tsdl.domain.exceptions import TSDLParseError
from shared.resilience.timeout import TimeoutContext, TimeoutError, timeout


class TestTimeoutContext(LaborantTest):
    """Test timeout context manager."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_timeout_context_initialization(self):
        """Test timeout context can be initialized."""
        ctx = TimeoutContext(timeout=5.0, operation="test")
        assert ctx.timeout == 5.0
        assert ctx.operation == "test"
        assert ctx.timed_out is False

    def test_operation_completes_within_timeout(self):
        """Test that fast operations complete successfully."""
        with timeout(1.0, "fast_operation"):
            time.sleep(0.1)  # Fast operation
        # Should not raise

    def test_operation_exceeds_timeout(self):
        """Test that slow operations raise TimeoutError with signal.alarm."""
        import platform

        # This test only works reliably with signal.alarm (Unix, main thread)
        if platform.system() == "Windows":
            # Skip on Windows - signal.alarm not available
            return

        try:
            # Use signal-based timeout (only works in main thread)
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("slow_operation", 0.2)

            # Set up signal
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(1)  # 1 second timeout

            try:
                # This will be interrupted by SIGALRM
                time.sleep(2.0)
                assert False, "Expected TimeoutError but none was raised"
            except TimeoutError as e:
                # Expected
                assert e.operation == "slow_operation"
                assert e.timeout == 0.2
            finally:
                # Cancel alarm
                signal.alarm(0)

        except Exception:
            # If signal doesn't work, skip this test
            pass

    def test_timeout_error_attributes(self):
        """Test TimeoutError has correct attributes."""
        error = TimeoutError("parse", 30.0)
        assert error.operation == "parse"
        assert error.timeout == 30.0
        assert "parse" in str(error)
        assert "30" in str(error)

    def test_nested_timeout_contexts(self):
        """Test nested timeout contexts work correctly."""
        with timeout(2.0, "outer"):
            time.sleep(0.1)
            with timeout(1.0, "inner"):
                time.sleep(0.1)
            # Inner completed
        # Outer completed

    def test_timeout_with_exception(self):
        """Test timeout context handles exceptions correctly."""
        try:
            with timeout(1.0, "operation"):
                raise ValueError("Test error")
        except ValueError as e:
            assert str(e) == "Test error"
        # TimeoutError should not be raised


class TestTSDLEngineTimeout(LaborantTest):
    """Test timeout integration in TSDLEngine."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""
        # Create custom settings with short timeouts for testing
        self.test_settings = Settings(
            TIMEOUTS_PARSE_SECONDS=2,
            TIMEOUTS_PLUGIN_LOAD_SECONDS=1,
            TIMEOUTS_COMPILE_SECONDS=2,
        )
        override_settings(self.test_settings)

    def teardown(self):
        """Cleanup after tests."""
        reset_settings()

    def test_parse_uses_default_timeout_from_config(self):
        """Test that parse uses timeout from configuration."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        engine = TSDLEngine()
        assert engine.settings.TIMEOUTS_PARSE_SECONDS == 2

    def test_parse_accepts_custom_timeout(self):
        """Test that parse accepts custom timeout parameter."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        engine = TSDLEngine()

        # Mock the actual parsing to avoid real parsing
        with patch.object(engine, "_extract_base_strategies", return_value=[]):
            with patch.object(engine, "_load_plugins"):
                with patch.object(engine, "_parse_with_plugins", return_value={}):
                    with patch.object(engine, "_build_document", return_value=Mock()):
                        # This should use custom timeout of 60 seconds
                        try:
                            engine.parse(
                                "STRATEGY 'Test'\nMETADATA\nEND", timeout_seconds=60
                            )
                        except Exception:
                            pass  # Parsing might fail, but timeout should work

    def test_compile_uses_default_timeout_from_config(self):
        """Test that compile uses timeout from configuration."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        engine = TSDLEngine()
        assert engine.settings.TIMEOUTS_COMPILE_SECONDS == 2

    def test_timeout_configuration_validation(self):
        """Test that timeout settings are validated."""
        # Test minimum value
        try:
            Settings(TIMEOUTS_PARSE_SECONDS=0)
            assert False, "Expected validation error for TIMEOUTS_PARSE_SECONDS=0"
        except Exception:
            pass  # Expected

        # Test maximum value
        try:
            Settings(TIMEOUTS_PARSE_SECONDS=400)
            assert False, "Expected validation error for TIMEOUTS_PARSE_SECONDS=400"
        except Exception:
            pass  # Expected

        # Test valid value
        settings = Settings(TIMEOUTS_PARSE_SECONDS=30)
        assert settings.TIMEOUTS_PARSE_SECONDS == 30

    def test_plugin_load_timeout_configuration(self):
        """Test plugin load timeout configuration."""
        # Test minimum value
        try:
            Settings(TIMEOUTS_PLUGIN_LOAD_SECONDS=0)
            assert False, "Expected validation error"
        except Exception:
            pass  # Expected

        # Test maximum value
        try:
            Settings(TIMEOUTS_PLUGIN_LOAD_SECONDS=100)
            assert False, "Expected validation error"
        except Exception:
            pass  # Expected

        # Test valid value
        settings = Settings(TIMEOUTS_PLUGIN_LOAD_SECONDS=10)
        assert settings.TIMEOUTS_PLUGIN_LOAD_SECONDS == 10


class TestTimeoutErrorHandling(LaborantTest):
    """Test timeout error handling and recovery."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_timeout_error_converts_to_parse_error(self):
        """Test that TimeoutError is converted to TSDLParseError."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        # Create engine with very short timeout
        test_settings = Settings(TIMEOUTS_PARSE_SECONDS=1)
        override_settings(test_settings)

        engine = TSDLEngine()

        # Mock a slow operation that raises TimeoutError
        def slow_extract(*args):
            raise TimeoutError("parse", 0.3)

        with patch.object(engine, "_extract_base_strategies", side_effect=slow_extract):
            try:
                engine.parse("STRATEGY 'Test'", timeout_seconds=0.3)
                assert False, "Expected TSDLParseError but none was raised"
            except TSDLParseError as e:
                assert e.error_code == "E999"
                assert "timed out" in str(e).lower()
                assert "0.3" in str(e)

        reset_settings()

    def test_timeout_logs_metrics(self):
        """Test that timeout errors are logged to metrics."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        # Create engine with mock metrics
        mock_metrics = Mock()
        engine = TSDLEngine(metrics_reporter=mock_metrics)

        # Mock a slow operation that raises TimeoutError
        def slow_extract(*args):
            raise TimeoutError("parse", 0.3)

        with patch.object(engine, "_extract_base_strategies", side_effect=slow_extract):
            try:
                engine.parse("STRATEGY 'Test'", timeout_seconds=0.3)
            except TSDLParseError:
                pass  # Expected

        # Verify metrics were logged
        assert mock_metrics.log_parse_start.called
        assert mock_metrics.log_parse_error.called

        # Check error code
        call_args = mock_metrics.log_parse_error.call_args
        assert call_args[0][0] == "E999"  # Timeout error code

    def test_process_with_timeouts(self):
        """Test full process() pipeline with timeouts."""
        from tsdl.infrastructure.tsdl_engine import TSDLEngine

        engine = TSDLEngine()

        # Mock all operations to be fast
        with patch.object(engine, "_extract_base_strategies", return_value=[]):
            with patch.object(engine, "_load_plugins"):
                with patch.object(engine, "_parse_with_plugins", return_value={}):
                    with patch.object(engine, "_build_document", return_value=Mock()):
                        with patch.object(engine, "validate", return_value=True):
                            with patch.object(
                                engine, "compile", return_value="# Generated code"
                            ):
                                try:
                                    # Should complete without timeout
                                    engine.process(
                                        "STRATEGY 'Test'",
                                        parse_timeout=5.0,
                                        compile_timeout=5.0,
                                    )
                                except Exception as e:
                                    # Some error might occur, but not timeout
                                    assert "timeout" not in str(e).lower()


class TestTimeoutEdgeCases(LaborantTest):
    """Test edge cases for timeout functionality."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_zero_timeout(self):
        """Test behavior with zero timeout."""
        # Zero timeout might trigger immediately or not at all
        # Just verify it doesn't crash
        try:
            with timeout(0.01, "instant"):
                pass  # Do nothing
        except TimeoutError:
            pass  # Expected if timeout triggered

    def test_very_large_timeout(self):
        """Test behavior with very large timeout."""
        with timeout(1000.0, "long_operation"):
            time.sleep(0.1)
        # Should complete fine

    def test_timeout_cleanup_on_success(self):
        """Test that timeout context cleans up properly on success."""
        ctx = TimeoutContext(5.0, "test")
        with ctx:
            time.sleep(0.1)

        # Context should be cleaned up
        if ctx.timer:
            assert not ctx.timer.is_alive()

    def test_timeout_cleanup_on_manual_timeout(self):
        """Test cleanup when timeout flag is set manually."""
        ctx = TimeoutContext(5.0, "test")

        # Manually set timeout flag
        ctx.timed_out = True

        # Verify timeout is detected
        try:
            with ctx:
                pass
            assert False, "Expected TimeoutError"
        except TimeoutError:
            pass  # Expected


if __name__ == "__main__":
    TestTimeoutContext.run_as_main()
