"""
OpenTelemetry distributed tracing support.

Provides instrumentation for distributed tracing across microservices.
Supports multiple exporters: Console, OTLP (Jaeger, Tempo, etc).

Key Concepts:
- Span: Single unit of work (function call, HTTP request)
- Trace: Collection of spans representing end-to-end flow
- Context Propagation: Passing trace context between services

Example:
    from shared.observability import TracingConfig, setup_tracing, trace_span

    # Setup tracing
    config = TracingConfig(
        service_name="prophet",
        exporter_type="otlp",
        otlp_endpoint="http://jaeger:4318"
    )
    tracer = setup_tracing(config)

    # Trace a function
    @trace_span("process_strategy")
    def process_strategy(strategy_id: str):
        with tracer.start_as_current_span("parse_tsdl"):
            # Parse TSDL code
            pass

        with tracer.start_as_current_span("compile"):
            # Compile to Python
            pass
"""

import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

logger = logging.getLogger(__name__)


@dataclass
class TracingConfig:
    """Configuration for OpenTelemetry tracing."""

    service_name: str
    """Name of the service (e.g., 'prophet', 'chevalier')"""

    exporter_type: str = "console"
    """Type of exporter: 'console', 'otlp'"""

    otlp_endpoint: Optional[str] = None
    """OTLP endpoint URL (e.g., 'http://jaeger:4318')"""

    environment: str = "development"
    """Environment name (development, production)"""

    sample_rate: float = 1.0
    """Sampling rate (0.0 to 1.0, default: 1.0 = trace everything)"""


class TracingManager:
    """
    Manages OpenTelemetry tracing setup and lifecycle.

    Handles tracer provider initialization, exporter configuration,
    and graceful shutdown.
    """

    def __init__(self, config: TracingConfig):
        """
        Initialize tracing manager.

        Args:
            config: Tracing configuration
        """
        self.config = config
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self._initialized = False

    def setup(self) -> trace.Tracer:
        """
        Setup OpenTelemetry tracing.

        Returns:
            Configured tracer instance

        Raises:
            ValueError: If exporter type is invalid
        """
        if self._initialized:
            logger.warning("Tracing already initialized")
            return self.tracer

        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": self.config.service_name,
                "service.environment": self.config.environment,
            }
        )

        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)

        # Configure exporter
        if self.config.exporter_type == "console":
            exporter = ConsoleSpanExporter()
            logger.info("Using Console span exporter")

        elif self.config.exporter_type == "otlp":
            if not self.config.otlp_endpoint:
                raise ValueError("otlp_endpoint required for OTLP exporter")

            exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
            logger.info(f"Using OTLP span exporter: {self.config.otlp_endpoint}")

        else:
            raise ValueError(f"Invalid exporter type: {self.config.exporter_type}")

        # Add span processor
        span_processor = BatchSpanProcessor(exporter)
        self.tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        self._initialized = True

        logger.info(f"Tracing initialized for service: {self.config.service_name}")

        return self.tracer

    def shutdown(self) -> None:
        """Shutdown tracing and flush remaining spans."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Tracing shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if tracing is initialized."""
        return self._initialized


def setup_tracing(config: TracingConfig) -> trace.Tracer:
    """
    Setup OpenTelemetry tracing with given configuration.

    Convenience function to initialize tracing.

    Args:
        config: Tracing configuration

    Returns:
        Configured tracer instance

    Example:
        config = TracingConfig(service_name="prophet")
        tracer = setup_tracing(config)
    """
    manager = TracingManager(config)
    return manager.setup()


def trace_span(span_name: str, attributes: Optional[dict] = None):
    """
    Decorator to automatically trace a function.

    Creates a span for the decorated function with optional attributes.

    Args:
        span_name: Name of the span
        attributes: Additional attributes to add to span

    Example:
        @trace_span("process_order", {"order.type": "market"})
        def process_order(order_id: str):
            # Function logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function arguments as attributes
                if args:
                    span.set_attribute("args.count", len(args))

                if kwargs:
                    for key, value in kwargs.items():
                        # Only add simple types
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"arg.{key}", value)

                # Execute function
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result

                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    """
    Get tracer instance.

    Args:
        name: Tracer name (default: __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name or __name__)


def add_span_attribute(key: str, value: Any) -> None:
    """
    Add attribute to current span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[dict] = None) -> None:
    """
    Add event to current span.

    Args:
        name: Event name
        attributes: Event attributes
    """
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


__all__ = [
    "TracingConfig",
    "TracingManager",
    "setup_tracing",
    "trace_span",
    "get_tracer",
    "add_span_attribute",
    "add_span_event",
]
