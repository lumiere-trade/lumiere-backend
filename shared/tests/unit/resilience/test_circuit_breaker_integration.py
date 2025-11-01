"""
Integration tests for CircuitBreaker with TSDLEngine.

Tests circuit breaker protecting plugin loading.

Usage:
    python -m tests.unit.infrastructure.resilience.test_circuit_breaker_integration
"""

from unittest.mock import Mock, patch

from tsdl.domain.exceptions import TSDLParseError
from tsdl.infrastructure.tsdl_engine import TSDLEngine

from shared.resilience import CircuitBreakerState
from shared.tests import LaborantTest


class TestCircuitBreakerIntegration(LaborantTest):
    """Test circuit breaker integration with TSDLEngine."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""
        self.engine = TSDLEngine()

    def test_engine_has_circuit_breaker(self):
        """Test TSDLEngine initializes with circuit breaker."""
        assert self.engine.plugin_breaker is not None
        assert self.engine.plugin_breaker.name == "plugin_loader"
        assert self.engine.plugin_breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_can_be_disabled(self):
        """Test circuit breaker can be disabled via config."""
        from tsdl.config import Settings, override_settings

        # Disable circuit breaker
        settings = Settings(CIRCUIT_BREAKER_ENABLED=False)
        override_settings(settings)

        try:
            engine = TSDLEngine()
            assert engine.plugin_breaker is None
        finally:
            # Reset settings
            from tsdl.config import reset_settings

            reset_settings()

    def test_circuit_breaker_wraps_plugin_loading(self):
        """Test circuit breaker wraps plugin loading with mock."""
        # Mock validation to pass
        with patch.object(self.engine.registry, "validate_composition") as mock_val:
            mock_val.return_value = (True, [])

            # Mock registry to simulate plugin failure
            with patch.object(self.engine.registry, "get_plugin") as mock_get:
                mock_get.side_effect = Exception("Plugin load failed")

                tsdl_source = """STRATEGY "Test"
METADATA
    AUTHOR: "Test"
    VERSION: "1.0.0"
    DESCRIPTION: "Test"
    STRATEGY_COMPOSITION:
        BASE_STRATEGIES: test_plugin
    END
END
ASSET
    SYMBOL: BTC/USD
    TIMEFRAME: 1h
END
RISK_MANAGEMENT
    MAX_POSITIONS: 1
END
POSITION_SIZING
    METHOD: fixed
    SIZE: 100
END"""

                # Try to parse - should fail
                try:
                    self.engine.parse(tsdl_source)
                except Exception:
                    pass

                # Circuit breaker should have recorded failure
                assert self.engine.plugin_breaker.failure_count >= 1

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after threshold failures."""
        # Create new engine
        engine = TSDLEngine()
        threshold = engine.plugin_breaker.config.failure_threshold

        # Mock validation and registry
        with patch.object(engine.registry, "validate_composition") as mock_val:
            mock_val.return_value = (True, [])

            with patch.object(engine.registry, "get_plugin") as mock_get:
                mock_get.side_effect = Exception("Plugin failed")

                tsdl_source = """STRATEGY "Test"
METADATA
    AUTHOR: "Test"
    VERSION: "1.0.0"
    DESCRIPTION: "Test"
    STRATEGY_COMPOSITION:
        BASE_STRATEGIES: test_plugin
    END
END
ASSET
    SYMBOL: BTC/USD
    TIMEFRAME: 1h
END
RISK_MANAGEMENT
    MAX_POSITIONS: 1
END
POSITION_SIZING
    METHOD: fixed
    SIZE: 100
END"""

                # Fail threshold times
                for i in range(threshold):
                    try:
                        engine.parse(tsdl_source)
                    except Exception:
                        pass

        # Circuit breaker should be open
        assert engine.plugin_breaker.state == CircuitBreakerState.OPEN

    def test_open_breaker_rejects_plugin_load(self):
        """Test open circuit breaker rejects plugin loading."""
        # Create new engine and trip the breaker
        engine = TSDLEngine()
        engine.plugin_breaker.trip()

        # Mock validation to pass (so we reach plugin loading)
        with patch.object(engine.registry, "validate_composition") as mock_val:
            mock_val.return_value = (True, [])

            tsdl_source = """STRATEGY "Test"
METADATA
    AUTHOR: "Test"
    VERSION: "1.0.0"
    DESCRIPTION: "Test"
    STRATEGY_COMPOSITION:
        BASE_STRATEGIES: test_plugin
    END
END
ASSET
    SYMBOL: BTC/USD
    TIMEFRAME: 1h
END
RISK_MANAGEMENT
    MAX_POSITIONS: 1
END
POSITION_SIZING
    METHOD: fixed
    SIZE: 100
END"""

            # Try to parse - should fail with E201
            try:
                engine.parse(tsdl_source)
                assert False, "Expected TSDLParseError with E201"
            except TSDLParseError as e:
                assert e.error_code == "E201"
                assert "circuit breaker" in e.message.lower()
                assert "OPEN" in e.message

    def test_manual_breaker_reset_works(self):
        """Test manual circuit breaker reset."""
        # Trip the breaker
        self.engine.plugin_breaker.trip()
        assert self.engine.plugin_breaker.state == CircuitBreakerState.OPEN

        # Reset it
        self.engine.plugin_breaker.reset()
        assert self.engine.plugin_breaker.state == CircuitBreakerState.CLOSED

    def test_get_circuit_breaker_stats(self):
        """Test getting circuit breaker statistics."""
        stats = self.engine.get_circuit_breaker_stats()

        assert stats is not None
        assert stats["name"] == "plugin_loader"
        assert stats["state"] == "closed"
        assert "config" in stats

    def test_circuit_breaker_stats_when_disabled(self):
        """Test stats return None when breaker disabled."""
        from tsdl.config import Settings, override_settings, reset_settings

        settings = Settings(CIRCUIT_BREAKER_ENABLED=False)
        override_settings(settings)

        try:
            engine = TSDLEngine()
            stats = engine.get_circuit_breaker_stats()
            assert stats is None
        finally:
            reset_settings()

    def test_successful_plugin_load_with_mock(self):
        """Test successful plugin loading doesn't trip breaker."""
        # Mock successful plugin loading
        mock_plugin = Mock()
        mock_plugin.register_keywords = Mock()

        with patch.object(self.engine.registry, "validate_composition") as mock_val:
            mock_val.return_value = (True, [])

            with patch.object(self.engine.registry, "get_plugin") as mock_get:
                mock_get.return_value = mock_plugin

                tsdl_source = """STRATEGY "Test"
METADATA
    AUTHOR: "Test"
    VERSION: "1.0.0"
    DESCRIPTION: "Test"
    STRATEGY_COMPOSITION:
        BASE_STRATEGIES: test_plugin
    END
END
ASSET
    SYMBOL: BTC/USD
    TIMEFRAME: 1h
END
RISK_MANAGEMENT
    MAX_POSITIONS: 1
END
POSITION_SIZING
    METHOD: fixed
    SIZE: 100
END"""

                # This should succeed (mock parse/validate steps too)
                with patch.object(self.engine, "_parse_with_plugins"):
                    with patch.object(self.engine, "_build_document"):
                        try:
                            self.engine.parse(tsdl_source)
                        except Exception:
                            pass  # Ignore other errors

        # Circuit breaker should still be closed
        assert self.engine.plugin_breaker.state == CircuitBreakerState.CLOSED


class TestCircuitBreakerConfiguration(LaborantTest):
    """Test circuit breaker configuration from settings."""

    component_name = "tsdl"
    test_category = "unit"

    def setup(self):
        """Setup test fixtures."""

    def test_custom_circuit_breaker_config(self):
        """Test circuit breaker uses custom configuration."""
        from tsdl.config import Settings, override_settings, reset_settings

        settings = Settings(
            CIRCUIT_BREAKER_ENABLED=True,
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=10,
            CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3,
            CIRCUIT_BREAKER_TIMEOUT=120,
            CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=5,
        )
        override_settings(settings)

        try:
            engine = TSDLEngine()

            assert engine.plugin_breaker is not None
            assert engine.plugin_breaker.config.failure_threshold == 10
            assert engine.plugin_breaker.config.success_threshold == 3
            assert engine.plugin_breaker.config.timeout == 120.0
            assert engine.plugin_breaker.config.half_open_max_calls == 5
        finally:
            reset_settings()

    def test_default_circuit_breaker_config(self):
        """Test circuit breaker uses default configuration."""
        from tsdl.config import reset_settings

        reset_settings()
        engine = TSDLEngine()

        assert engine.plugin_breaker is not None
        assert engine.plugin_breaker.config.failure_threshold == 5
        assert engine.plugin_breaker.config.success_threshold == 2
        assert engine.plugin_breaker.config.timeout == 60.0
        assert engine.plugin_breaker.config.half_open_max_calls == 3


if __name__ == "__main__":
    TestCircuitBreakerIntegration.run_as_main()
