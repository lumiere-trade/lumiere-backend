"""
System Reporter - Centralized logging with optional Courier integration.

Provides SystemReporter for file/console logging with optional Courier
integration for real-time UI broadcasting.

Production-ready: Supports stdout logging for Docker environments.
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime
from typing import Any, Optional

# Constants
LOG_RETENTION_DAYS = 1
LOG_CHECK_INTERVAL = 3600  # 1 hour


class SystemReporter:
    """
    Logger with verbose filtering and optional Courier integration.

    Supports both file-based logging (development) and stdout logging
    (production Docker).

    Verbose Levels:
        0 = Critical only (always visible)
        1 = Important messages (default)
        2 = Detailed information
        3 = Debug/verbose
    """

    def __init__(
        self,
        name: str = "system",
        log_dir: Optional[str] = None,
        level: int = logging.INFO,
        verbose: int = 1,
        courier_client: Optional[Any] = None,
    ) -> None:
        """
        Initialize SystemReporter.

        Args:
            name: Logger name (used for filename if log_dir provided)
            log_dir: Directory for log files. If None, logs to stdout only.
                    Can be relative ("logs") or absolute ("/app/logs")
            level: Python logging level
            verbose: Verbosity filter (0-3)
            courier_client: Optional CourierClient for UI broadcasting
        """
        self.name = name
        self.verbose = verbose
        self.courier_client = courier_client
        self.courier_available = False

        # Check Courier availability if provided
        if self.courier_client:
            try:
                self.courier_available = self.courier_client.health_check_sync()
            except Exception:
                self.courier_available = False

        # Initialize logging
        self._init_logger(name, log_dir, level)

    def _init_logger(
        self, name: str, log_dir: Optional[str], level: int
    ) -> None:
        """
        Initialize logger with file and/or console handlers.

        Args:
            name: Logger name
            log_dir: Log directory path (None = stdout only)
            level: Python logging level
        """
        # Initialize logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Always add console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add file handler only if log_dir provided
        if log_dir:
            # Handle absolute vs relative paths
            if os.path.isabs(log_dir):
                # Absolute path - use as-is
                log_file = os.path.join(log_dir, f"{name}.log")
            else:
                # Relative path - resolve from package location
                base_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..")
                )
                log_file = os.path.join(base_dir, log_dir, f"{name}.log")

            # Create log directory
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # Clear old log file
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                    print(
                        f"✓ Cleared old log file: {log_file}",
                        file=sys.stderr,
                    )
                except Exception as e:
                    print(
                        f"⚠ Could not clear old log file: {e}",
                        file=sys.stderr,
                    )

            # File handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Start log retention worker
            retention_thread = threading.Thread(
                target=self._log_retention_worker,
                args=(log_file,),
                daemon=True,
            )
            retention_thread.start()

            log_dest = log_file
        else:
            log_dest = "stdout"

        courier_status = "with Courier" if self.courier_client else "logging only"
        if self.courier_client and not self.courier_available:
            courier_status += " (unavailable)"

        print(
            f"✓ SystemReporter initialized ({courier_status}): {log_dest}",
            file=sys.stderr,
        )

    def _log_retention_worker(self, log_file: str) -> None:
        """Background worker to rotate old log files."""
        while True:
            try:
                if os.path.exists(log_file):
                    mtime = os.path.getmtime(log_file)
                    age_days = (time.time() - mtime) / 86400

                    if age_days > LOG_RETENTION_DAYS:
                        os.remove(log_file)
                        print(
                            f"✓ Rotated log file (older than "
                            f"{LOG_RETENTION_DAYS} days): {log_file}",
                            file=sys.stderr,
                        )

                time.sleep(LOG_CHECK_INTERVAL)

            except Exception as e:
                print(
                    f"⚠ Retention worker error: {e}",
                    file=sys.stderr,
                )
                time.sleep(LOG_CHECK_INTERVAL)

    def _send_to_courier(
        self, level: str, message: str, context: str, verbose_level: int
    ) -> None:
        """Send log message to Courier (fire-and-forget)."""
        if not self.courier_client:
            return

        try:
            payload = {
                "type": "system_log",
                "level": level,
                "message": message,
                "context": context,
                "verbose_level": verbose_level,
                "timestamp": datetime.now().isoformat(),
            }

            success = self.courier_client.publish_sync("sys", payload)

            if not success and self.courier_available:
                self.courier_available = False
                print(f"⚠ Courier became unavailable", file=sys.stderr)
            elif success and not self.courier_available:
                self.courier_available = True
                print(f"✓ Courier connection restored", file=sys.stderr)

        except Exception as e:
            print(f"⚠ Courier publishing failed: {e}", file=sys.stderr)

    def set_verbose(self, level: int) -> None:
        """Update verbosity level."""
        self.verbose = max(0, min(3, level))
        self.info(
            f"Verbosity set to {self.verbose}",
            context="SystemReporter",
            verbose_level=0,
        )

    def _should_log(self, verbose_level: int) -> bool:
        """Check if message should be logged."""
        return self.verbose >= verbose_level

    # Core logging methods
    def debug(
        self, msg: str, context: str = "system", verbose_level: int = 3
    ) -> None:
        """Log debug message (not sent to Courier)."""
        if self._should_log(verbose_level):
            formatted_msg = f"[{context}] {msg}"
            self.logger.debug(formatted_msg)

    def info(
        self, msg: str, context: str = "system", verbose_level: int = 1
    ) -> None:
        """Log info message and send to Courier (if available)."""
        if self._should_log(verbose_level):
            formatted_msg = f"[{context}] {msg}"
            self.logger.info(formatted_msg)
            self._send_to_courier("info", msg, context, verbose_level)

    def warning(
        self, msg: str, context: str = "system", verbose_level: int = 1
    ) -> None:
        """Log warning message and send to Courier (if available)."""
        if self._should_log(verbose_level):
            formatted_msg = f"[{context}] {msg}"
            self.logger.warning(formatted_msg)
            self._send_to_courier("warning", msg, context, verbose_level)

    def error(
        self, msg: str, context: str = "system", verbose_level: int = 0
    ) -> None:
        """Log error message and send to Courier (if available)."""
        if self._should_log(verbose_level):
            formatted_msg = f"[{context}] {msg}"
            self.logger.error(formatted_msg)
            self._send_to_courier("error", msg, context, verbose_level)

    def critical(
        self, msg: str, context: str = "system", verbose_level: int = 0
    ) -> None:
        """Log critical message and send to Courier (if available)."""
        if self._should_log(verbose_level):
            formatted_msg = f"[{context}] {msg}"
            self.logger.critical(formatted_msg)
            self._send_to_courier("critical", msg, context, verbose_level)
