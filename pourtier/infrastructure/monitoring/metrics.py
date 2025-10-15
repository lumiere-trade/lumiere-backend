"""
Prometheus metrics collection.
"""

from prometheus_client import Counter, Gauge, Histogram

# ============================================================
# HTTP Metrics
# ============================================================

http_requests_total = Counter(
    "pourtier_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "pourtier_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_errors_total = Counter(
    "pourtier_http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)

# ============================================================
# Database Metrics
# ============================================================

db_queries_total = Counter(
    "pourtier_db_queries_total",
    "Total database queries",
    ["operation"],
)

db_query_duration_seconds = Histogram(
    "pourtier_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

db_pool_size = Gauge(
    "pourtier_db_pool_size",
    "Database connection pool size",
)

db_pool_checked_out = Gauge(
    "pourtier_db_pool_checked_out",
    "Database connections currently checked out",
)

# ============================================================
# Cache Metrics
# ============================================================

cache_hits_total = Counter(
    "pourtier_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "pourtier_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

cache_operations_total = Counter(
    "pourtier_cache_operations_total",
    "Total cache operations",
    ["operation", "cache_type"],
)

# ============================================================
# Blockchain Metrics
# ============================================================

blockchain_requests_total = Counter(
    "pourtier_blockchain_requests_total",
    "Total blockchain requests",
    ["service", "operation"],
)

blockchain_errors_total = Counter(
    "pourtier_blockchain_errors_total",
    "Total blockchain errors",
    ["service", "error_type"],
)

blockchain_request_duration_seconds = Histogram(
    "pourtier_blockchain_request_duration_seconds",
    "Blockchain request duration in seconds",
    ["service", "operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

circuit_breaker_state = Gauge(
    "pourtier_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
)

# ============================================================
# Business Metrics
# ============================================================

active_users_total = Gauge(
    "pourtier_active_users_total",
    "Total active users",
)

escrow_balance_total = Gauge(
    "pourtier_escrow_balance_total",
    "Total escrow balance in USD",
)

subscriptions_active_total = Gauge(
    "pourtier_subscriptions_active_total",
    "Total active subscriptions",
    ["plan_type"],
)
