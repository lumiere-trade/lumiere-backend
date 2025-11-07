"""
Observability utilities for microservices.

Provides:
- Prometheus metrics server
- OpenTelemetry distributed tracing
"""

from shared.observability.metrics_server import (
    MetricsServer,
    run_metrics_server,
)
from shared.observability.tracing import (
    TracingConfig,
    TracingManager,
    add_span_attribute,
    add_span_event,
    get_tracer,
    setup_tracing,
    trace_span,
)

__all__ = [
    # Metrics
    "MetricsServer",
    "run_metrics_server",
    # Tracing
    "TracingConfig",
    "TracingManager",
    "setup_tracing",
    "trace_span",
    "get_tracer",
    "add_span_attribute",
    "add_span_event",
]
