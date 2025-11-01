"""
Unit tests for OpenTelemetry Tracing.

Tests tracing setup, span creation, decorators, and context propagation.

Usage:
    python tests/unit/observability/test_tracing.py
    laborant test shared --unit
"""

import time
from shared.tests import LaborantTest
from shared.observability import (
    TracingConfig,
    TracingManager,
    setup_tracing,
    trace_span,
    get_tracer,
    add_span_attribute,
    add_span_event,
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)


class InMemorySpanExporter:
    """Simple in-memory span exporter for testing."""

    def __init__(self):
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return 0  # Success

    def shutdown(self):
        pass

    def get_finished_spans(self):
        return self.spans

    def clear(self):
        self.spans = []


class TestTracingConfig(LaborantTest):
    """Unit tests for TracingConfig."""

    component_name = "shared"
    test_category = "unit"

    def test_tracing_config_defaults(self):
        """Test TracingConfig default values."""
        self.reporter.info("Testing TracingConfig defaults", context="Test")

        config = TracingConfig(service_name="test-service")

        assert config.service_name == "test-service"
        assert config.exporter_type == "console"
        assert config.otlp_endpoint is None
        assert config.environment == "development"
        assert config.sample_rate == 1.0

        self.reporter.info("Default config values correct", context="Test")

    def test_tracing_config_custom_values(self):
        """Test TracingConfig with custom values."""
        self.reporter.info("Testing custom TracingConfig", context="Test")

        config = TracingConfig(
            service_name="prophet",
            exporter_type="otlp",
            otlp_endpoint="http://jaeger:4318",
            environment="production",
            sample_rate=0.5,
        )

        assert config.service_name == "prophet"
        assert config.exporter_type == "otlp"
        assert config.otlp_endpoint == "http://jaeger:4318"
        assert config.environment == "production"
        assert config.sample_rate == 0.5

        self.reporter.info("Custom config values correct", context="Test")


class TestTracingManager(LaborantTest):
    """Unit tests for TracingManager."""

    component_name = "shared"
    test_category = "unit"

    def test_tracing_manager_initialization(self):
        """Test TracingManager initialization."""
        self.reporter.info("Testing manager initialization", context="Test")

        config = TracingConfig(service_name="test-service")
        manager = TracingManager(config)

        assert manager.config.service_name == "test-service"
        assert manager.is_initialized is False
        assert manager.tracer is None

        self.reporter.info("Manager initialized correctly", context="Test")

    def test_tracing_manager_setup_console(self):
        """Test TracingManager setup with console exporter."""
        self.reporter.info("Testing console exporter setup", context="Test")

        config = TracingConfig(
            service_name="test-console",
            exporter_type="console"
        )
        manager = TracingManager(config)
        tracer = manager.setup()

        assert manager.is_initialized is True
        assert tracer is not None

        manager.shutdown()

        self.reporter.info("Console exporter setup successful", context="Test")

    def test_tracing_manager_setup_already_initialized(self):
        """Test setup returns same tracer if already initialized."""
        self.reporter.info("Testing double initialization", context="Test")

        config = TracingConfig(service_name="test-double")
        manager = TracingManager(config)

        tracer1 = manager.setup()
        tracer2 = manager.setup()

        assert tracer1 is tracer2
        assert manager.is_initialized is True

        manager.shutdown()

        self.reporter.info("Double initialization handled", context="Test")

    def test_tracing_manager_shutdown(self):
        """Test TracingManager shutdown."""
        self.reporter.info("Testing manager shutdown", context="Test")

        config = TracingConfig(service_name="test-shutdown")
        manager = TracingManager(config)
        manager.setup()

        assert manager.is_initialized is True

        manager.shutdown()

        self.reporter.info("Manager shutdown successful", context="Test")


class TestTracingDecorator(LaborantTest):
    """Unit tests for trace_span decorator."""

    component_name = "shared"
    test_category = "unit"

    def setup(self):
        """Setup test tracing with in-memory exporter."""
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        processor = SimpleSpanProcessor(self.exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def test_trace_span_decorator_basic(self):
        """Test trace_span decorator creates span."""
        self.reporter.info("Testing trace_span decorator", context="Test")

        @trace_span("test_operation")
        def test_function():
            return "success"

        result = test_function()

        assert result == "success"

        # Check span was created
        spans = self.exporter.get_finished_spans()
        assert len(spans) > 0
        assert spans[-1].name == "test_operation"

        self.reporter.info("Decorator created span", context="Test")

    def test_trace_span_with_attributes(self):
        """Test trace_span decorator with custom attributes."""
        self.reporter.info("Testing span attributes", context="Test")

        @trace_span("test_with_attrs", {"custom.key": "custom_value"})
        def test_function(user_id: str):
            return f"Hello {user_id}"

        result = test_function("user123")

        assert result == "Hello user123"

        spans = self.exporter.get_finished_spans()
        span = spans[-1]

        assert span.name == "test_with_attrs"
        assert span.attributes.get("custom.key") == "custom_value"
        assert span.attributes.get("arg.user_id") == "user123"

        self.reporter.info("Attributes recorded correctly", context="Test")

    def test_trace_span_with_exception(self):
        """Test trace_span decorator records exceptions."""
        self.reporter.info("Testing exception recording", context="Test")

        @trace_span("test_with_error")
        def test_function():
            raise ValueError("Test error")

        try:
            test_function()
            assert False, "Should have raised exception"
        except ValueError:
            pass

        spans = self.exporter.get_finished_spans()
        span = spans[-1]

        assert span.attributes.get("status") == "error"
        assert span.attributes.get("error.type") == "ValueError"
        assert "Test error" in span.attributes.get("error.message")

        self.reporter.info("Exception recorded in span", context="Test")


class TestTracingUtilities(LaborantTest):
    """Unit tests for tracing utility functions."""

    component_name = "shared"
    test_category = "unit"

    def setup(self):
        """Setup test tracing with in-memory exporter."""
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        processor = SimpleSpanProcessor(self.exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def test_get_tracer(self):
        """Test get_tracer utility."""
        self.reporter.info("Testing get_tracer", context="Test")

        tracer = get_tracer("test-tracer")

        assert tracer is not None

        self.reporter.info("get_tracer working", context="Test")

    def test_add_span_attribute(self):
        """Test add_span_attribute utility."""
        self.reporter.info("Testing add_span_attribute", context="Test")

        tracer = get_tracer()

        with tracer.start_as_current_span("test_span") as span:
            add_span_attribute("test.key", "test_value")
            add_span_attribute("test.number", 42)

        spans = self.exporter.get_finished_spans()
        span = spans[-1]

        assert span.attributes.get("test.key") == "test_value"
        assert span.attributes.get("test.number") == 42

        self.reporter.info("Attributes added correctly", context="Test")

    def test_add_span_event(self):
        """Test add_span_event utility."""
        self.reporter.info("Testing add_span_event", context="Test")

        tracer = get_tracer()

        with tracer.start_as_current_span("test_span"):
            add_span_event("test_event", {"event.data": "test"})

        spans = self.exporter.get_finished_spans()
        span = spans[-1]

        assert len(span.events) > 0
        assert span.events[-1].name == "test_event"

        self.reporter.info("Event added correctly", context="Test")


class TestSetupTracing(LaborantTest):
    """Unit tests for setup_tracing convenience function."""

    component_name = "shared"
    test_category = "unit"

    def test_setup_tracing_console(self):
        """Test setup_tracing with console exporter."""
        self.reporter.info("Testing setup_tracing", context="Test")

        config = TracingConfig(
            service_name="test-setup",
            exporter_type="console"
        )
        tracer = setup_tracing(config)

        assert tracer is not None

        self.reporter.info("setup_tracing working", context="Test")


if __name__ == "__main__":
    TestTracingConfig.run_as_main()
    TestTracingManager.run_as_main()
    TestTracingDecorator.run_as_main()
    TestTracingUtilities.run_as_main()
    TestSetupTracing.run_as_main()
