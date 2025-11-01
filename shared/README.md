# Shared - Common Libraries

**Shared utilities and libraries used across all Lumiere services.**

---

## Overview

The Shared module provides common functionality used by all Lumiere components, including resilience patterns, observability tools, blockchain utilities, technical indicators, system reporting, and testing frameworks.

**Purpose:** Eliminate code duplication and provide consistent implementations across services.

**Version:** 0.2.4  
**Status:** Production Ready ✅

---

## Quick Start

### Installation
```bash
pip install --index-url http://localhost:9001/simple/ \
    --trusted-host localhost \
    shared==0.2.4
```

### Basic Usage
```python
# Resilience patterns
from shared.resilience import CircuitBreaker, with_timeout, Retry

# Health checks
from shared.health import HealthServer, HealthCheck

# Observability
from shared.observability import MetricsServer, setup_tracing

# Blockchain utilities
from shared.blockchain import SolanaClient

# Technical indicators
from shared.indicators import RSI, MACD
```

---

## Components

### Resilience Patterns

**Location:** `shared/resilience/`

Production-ready patterns for distributed systems.

**Patterns:**
- **Circuit Breaker** - Prevent cascading failures
- **Timeout Protection** - Prevent hanging operations
- **Retry Pattern** - Automatic retry with exponential backoff
- **Rate Limiting** - Token bucket rate limiter

**Example:**
```python
from shared.resilience import CircuitBreaker, with_timeout

# Circuit breaker
breaker = CircuitBreaker("external_api", CircuitBreakerConfig(
    failure_threshold=5,
    timeout=60.0
))
result = breaker.call(external_api.get_data, user_id="123")

# Timeout protection
@with_timeout(5.0)
def long_operation():
    return heavy_computation()
```

**Tests:** 51 tests (100% passing)

---

### Health Checks

**Location:** `shared/health/`

Kubernetes-compatible health check system.

**Endpoints:**
- `GET /health` - Overall health status
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

**Example:**
```python
from shared.health import HealthCheck, HealthStatus, HealthServer

class MyHealthCheck(HealthCheck):
    def check(self) -> HealthStatus:
        if self.is_database_connected():
            return HealthStatus.HEALTHY
        return HealthStatus.UNHEALTHY

health_server = HealthServer(MyHealthCheck(), port=8080)
health_server.start_in_background()
```

**Tests:** 12 tests (100% passing)

---

### Graceful Shutdown

**Location:** `shared/lifecycle/`

Handle SIGTERM/SIGINT for clean service termination.

**Example:**
```python
from shared.lifecycle import GracefulShutdown

shutdown = GracefulShutdown()

@shutdown.on_shutdown
async def cleanup():
    await db.close()
    await redis.close()

shutdown.wait_for_signal()
```

**Tests:** 8 tests (100% passing)

---

### Observability

**Location:** `shared/observability/`

Prometheus metrics and OpenTelemetry tracing.

**Features:**
- **Metrics Server** - HTTP /metrics endpoint for Prometheus
- **Distributed Tracing** - OpenTelemetry with OTLP export

**Example:**
```python
# Metrics
from shared.observability import MetricsServer
from prometheus_client import Counter

requests_total = Counter('requests_total', 'Total requests')
metrics_server = MetricsServer(port=9090)
metrics_server.start_in_background()

# Tracing
from shared.observability import setup_tracing, trace_span

config = TracingConfig(
    service_name="prophet",
    exporter_type="otlp",
    otlp_endpoint="http://jaeger:4318"
)
tracer = setup_tracing(config)

@trace_span("process_request")
def process_request(user_id: str):
    return result
```

**Tests:** 20 tests (100% passing)

---

### Blockchain Utilities

**Location:** `shared/blockchain/`

Solana blockchain interaction utilities.

**Modules:**
- `solana_client.py` - Solana RPC client wrapper
- `transaction_signer.py` - Transaction signing utilities
- `wallets.py` - Platform wallet management
- `escrow_helpers.py` - Escrow contract helpers

**Example:**
```python
from shared.blockchain import SolanaClient
from shared.blockchain.wallets import PlatformWallets

client = SolanaClient(
    rpc_url="https://api.devnet.solana.com",
    commitment="confirmed"
)

platform_wallet = PlatformWallets.get_platform_wallet()
alice = PlatformWallets.get_test_alice_address()
```

---

### Technical Indicators

**Location:** `shared/indicators/`

Technical analysis indicators for trading strategies.

**Available Indicators:**
- RSI, MACD, Bollinger Bands
- EMA, SMA, ATR, ADX
- Stochastic Oscillator
- Volume indicators
- Chart pattern detection

**Example:**
```python
from shared.indicators import RSI, MACD, BollingerBands

rsi = RSI(period=14)
rsi_value = rsi.calculate(price_data)

macd = MACD(fast=12, slow=26, signal=9)
macd_line, signal_line, histogram = macd.calculate(price_data)

bb = BollingerBands(period=20, std_dev=2)
upper, middle, lower = bb.calculate(price_data)
```

---

### System Reporter

**Location:** `shared/reporter/`

Structured logging and reporting system with emoji support.

**Features:**
- Color-coded log levels
- Context tracking
- Verbose levels (0-3)
- Emoji categories for visual identification
- File and console output

**Example:**
```python
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji

reporter = SystemReporter(
    name="my_service",
    log_dir="logs",
    verbose=1
)

reporter.info(f"{Emoji.SUCCESS} Operation completed", context="Service")
reporter.error(f"{Emoji.ERROR} Operation failed", context="Service")
```

---

### Test Framework

**Location:** `shared/tests/`

LaborantTest base class and testing utilities.

**Features:**
- Async test support
- Setup/teardown hooks
- Test categorization (unit/integration/e2e)
- Component mapping
- Result schema validation

**Example:**
```python
from shared.tests import LaborantTest

class TestMyFeature(LaborantTest):
    component_name = "my_service"
    test_category = "integration"
    
    async def test_feature_works(self):
        result = await self.client.call_feature()
        assert result == expected_value

if __name__ == "__main__":
    TestMyFeature.run_as_main()
```

---

## Documentation

- [RESILIENCE_GUIDE.md](docs/RESILIENCE_GUIDE.md) - Comprehensive guide (1000+ lines)

---

## Project Structure
```
shared/
├── resilience/              # Resilience patterns
│   ├── circuit_breaker.py
│   ├── timeout.py
│   ├── retry.py
│   ├── rate_limiter.py
│   └── exceptions.py
├── health/                  # Health check system
│   ├── health_check.py
│   ├── health_status.py
│   └── health_server.py
├── lifecycle/               # Service lifecycle
│   └── graceful_shutdown.py
├── observability/           # Monitoring and tracing
│   ├── metrics_server.py
│   └── tracing.py
├── blockchain/              # Blockchain utilities
│   ├── solana_client.py
│   ├── transaction_signer.py
│   ├── wallets.py
│   └── escrow_helpers.py
├── indicators/              # Technical indicators
│   ├── rsi.py, macd.py, bb.py
│   └── ...
├── reporter/                # System reporter
│   ├── system_reporter.py
│   └── emojis/
├── tests/                   # Test framework
│   └── test_base.py
├── docs/                    # Documentation
│   ├── RESILIENCE_GUIDE.md
│   └── README.md
└── pyproject.toml
```

---

## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Circuit Breaker | 20 | ✅ 100% |
| Timeout | 14 | ✅ 100% |
| Retry | 18 | ✅ 100% |
| Rate Limiting | 13 | ✅ 100% |
| Health Checks | 12 | ✅ 100% |
| Graceful Shutdown | 8 | ✅ 100% |
| Metrics Server | 7 | ✅ 100% |
| Tracing | 13 | ✅ 100% |
| **Total** | **105** | **✅ 100%** |

**Overall Coverage:** 98%+

---

## Dependencies

Core dependencies:
- `prometheus-client>=0.19.0` - Prometheus metrics
- `opentelemetry-api>=1.21.0` - OpenTelemetry tracing
- `opentelemetry-sdk>=1.21.0` - OpenTelemetry SDK
- `opentelemetry-exporter-otlp-proto-http>=1.21.0` - OTLP exporter
- `solders>=0.18.0` - Solana Python library
- `solana>=0.30.0` - Solana client
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `pyyaml>=6.0` - YAML configuration
- `requests>=2.31.0` - HTTP client

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.4 | Nov 1, 2025 | OpenTelemetry distributed tracing |
| 0.2.3 | Nov 1, 2025 | Prometheus Metrics Server |
| 0.2.2 | Nov 1, 2025 | Rate limiting (Token Bucket) |
| 0.2.1 | Nov 1, 2025 | Retry pattern with exponential backoff |
| 0.2.0 | Oct 31, 2025 | Circuit Breaker, Timeout, Health Checks, Graceful Shutdown |
| 0.1.5 | Oct 2025 | Reporter improvements |
| 0.1.0 | Sep 2025 | Initial release (SystemReporter) |

---

## Services Using Shared

- ✅ **TSDL** v2.1.0 (migrated to shared v0.2.4)
- **Prophet** (ready to integrate)
- **Pourtier** (ready to integrate)
- **Chevalier** (ready to integrate)
- **Cartographe** (ready to integrate)
- **All other services** (ready to integrate)

---

## Development

### Running Tests
```bash
# Run all tests
laborant test shared --all

# Run specific module
python tests/unit/resilience/test_circuit_breaker.py

# Run with coverage
pytest tests/ --cov=shared --cov-report=html
```

### Building Package
```bash
# Clean build
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Install locally
pip install --break-system-packages --force-reinstall dist/shared-0.2.4-py3-none-any.whl
```

---

## Best Practices

### Resilience Patterns
- Use circuit breakers for all external service calls
- Set realistic timeouts based on P95/P99 latency
- Only retry idempotent operations
- Use rate limiting to prevent abuse

### Health Checks
- Keep health checks fast (<100ms)
- Don't fail liveness for transient issues
- Fail readiness if dependencies are down
- Use separate port (8080) for health

### Observability
- Use consistent metric naming
- Add labels for dimensions
- Use sampling in production (0.1 = 10%)
- Propagate trace context between services

### Blockchain Operations
- Always use environment-specific wallets
- Never commit keypairs to git
- Use test wallets for development
- Verify transactions before processing

---

## Related Components

- [TSDL](../tsdl) - Uses resilience patterns
- [Pourtier](../pourtier) - Uses blockchain utilities
- [Prophet](../prophet) - Uses observability
- [Chevalier](../chevalier) - Uses health checks
- [Courier](../courier) - Uses system reporter

---

## Support

For questions or issues:
- Documentation: `/docs/`
- Tests: `/tests/`
- Email: dev@lumiere.trade

---

## License

Apache License 2.0

---

**Status:** Production Ready ✅  
**Version:** 0.2.4  
**Last Updated:** November 1, 2025
