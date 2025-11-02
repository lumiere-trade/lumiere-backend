"""
Database operations and data persistence emoji definitions.

Covers InfluxDB operations, candle storage, queries, and
bootstrap operations.

Usage:
    >>> from shared.reporter.emojis.database import DatabaseEmoji
    >>> print(f"{DatabaseEmoji.WRITE} Saved 100 records")
    💾 Saved 100 records
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class DatabaseEmoji(ComponentEmoji):
    """
    Database operations and data persistence.

    Categories:
        - CRUD: Create, Read, Update, Delete
        - Batch: Bulk operations, batching
        - Candles: Candle-specific operations
        - Initialization: Bootstrap, migration
    """

    # ============================================================
    # Basic CRUD Operations
    # ============================================================

    WRITE = "💾"  # Write/insert operation
    READ = "💾"  # Read/select operation
    UPDATE = "💾"  # Update operation
    DELETE = "💾"  # Delete operation
    QUERY = "🔍"  # Query execution

    # ============================================================
    # Batch Operations
    # ============================================================

    BATCH = "📦"  # Batch operation
    BULK = "📚"  # Bulk insert/update
    FLUSH = "💧"  # Flush buffers to disk
    COMMIT = "✔️"  # Transaction commit
    ROLLBACK = "↩️"  # Transaction rollback

    # ============================================================
    # Candle Operations
    # ============================================================

    CANDLE_SAVE = "💾"  # Candle data saved
    CANDLE_LOAD = "📊"  # Candle data loaded
    CANDLE_AGGREGATE = "⚙️"  # Candle aggregation
    CANDLE_BOOTSTRAP = "🔥"  # Candle bootstrap from API

    # ============================================================
    # Initialization & Maintenance
    # ============================================================

    BOOTSTRAP = "🔥"  # Initial data loading
    SEED = "🌱"  # Database seeding
    MIGRATE = "🔄"  # Database migration
    BACKUP = "💿"  # Database backup
    RESTORE = "📀"  # Database restore

    # ============================================================
    # Performance & Monitoring
    # ============================================================

    SLOW_QUERY = "🐌"  # Slow query detected
    FAST_QUERY = "⚡"  # Fast query
    INDEX = "📇"  # Index operation
    OPTIMIZE = "🔧"  # Database optimization
