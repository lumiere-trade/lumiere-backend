"""
Structured JSON logging configuration.
"""

import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any, Optional
from uuid import uuid4

# Context variable for request ID tracking
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format with consistent schema.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add standard fields
        if hasattr(record, "pathname"):
            log_data["file"] = record.pathname
            log_data["line"] = record.lineno
            log_data["function"] = record.funcName

        return json.dumps(log_data)


def setup_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Use JSON format (True) or plain text (False)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if json_logs:
        formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Silence httpx in test environments (reduce noise)
    if not json_logs:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger(
            "pourtier.presentation.api.middleware.request_id_middleware"
        ).setLevel(logging.WARNING)
        logging.getLogger(
            "pourtier.presentation.api.middleware.metrics_middleware"
        ).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.

    Args:
        request_id: Request ID (generates UUID if None)

    Returns:
        Request ID that was set
    """
    if request_id is None:
        request_id = str(uuid4())
    request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get request ID from current context.

    Returns:
        Request ID or None
    """
    return request_id_ctx.get()


def log_performance(logger: logging.Logger, operation: str, start_time: float) -> None:
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        start_time: Start timestamp from time.time()
    """
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{operation} completed",
        extra={
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
        },
    )
