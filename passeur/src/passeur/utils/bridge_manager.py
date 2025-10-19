"""
Bridge server manager for integration tests.

Manages starting/stopping the Node.js bridge server subprocess
for integration testing.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from shared.reporter.system_reporter import SystemReporter

from passeur.config.settings import load_config


class BridgeManager:
    """
    Manages Node.js bridge server lifecycle for tests.

    Starts bridge server as subprocess, waits for ready state,
    and ensures clean shutdown after tests.
    """

    def __init__(
        self,
        config_file: str = "test.yaml",
        env: str = "test",
        reporter: Optional[SystemReporter] = None,
    ):
        """
        Initialize bridge manager.

        Args:
            config_file: Config file to use (default: test.yaml)
            env: Environment name (test, development, production)
            reporter: Optional SystemReporter for logging
        """
        os.environ["ENV"] = env

        env_path = Path(__file__).parents[2] / f".env.{env}"
        if env_path.exists():
            load_dotenv(env_path)

        self.config = load_config(config_file)
        self.reporter = reporter or SystemReporter(
            name="bridge_manager", level=20, verbose=1
        )
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.bridge_url = f"http://{self.config.bridge_host}:{self.config.bridge_port}"

    def start(self, timeout: int = 30) -> bool:
        """
        Start bridge server subprocess.

        Args:
            timeout: Maximum seconds to wait for server ready

        Returns:
            True if server started successfully, False otherwise
        """
        if self.process is not None:
            self.reporter.warning("Bridge already running", context="BridgeManager")
            return True

        bridge_dir = Path("/app/bridge")

        if not bridge_dir.exists():
            self.reporter.error(
                f"Bridge directory not found: {bridge_dir}",
                context="BridgeManager",
            )
            return False

        server_js = bridge_dir / "server.js"
        if not server_js.exists():
            self.reporter.error(
                f"server.js not found: {server_js}",
                context="BridgeManager",
            )
            return False

        self.reporter.info("Starting bridge server...", context="BridgeManager")

        try:
            env = os.environ.copy()
            env["ENV"] = self.env

            self.process = subprocess.Popen(
                ["node", "server.js"],
                cwd=str(bridge_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            start_time = time.time()
            attempt = 0
            while time.time() - start_time < timeout:
                attempt += 1
                if self._is_ready():
                    self.reporter.info(
                        f"Bridge server ready after {attempt} attempts: "
                        f"{self.bridge_url}",
                        context="BridgeManager",
                    )
                    return True

                if self.process.poll() is not None:
                    stderr = self.process.stderr.read()
                    self.reporter.error(
                        f"Bridge server failed to start: {stderr}",
                        context="BridgeManager",
                    )
                    return False

                time.sleep(0.5)

            self.reporter.error(
                f"Bridge server timeout after {timeout}s ({attempt} attempts)",
                context="BridgeManager",
            )
            self.stop()
            return False

        except Exception as e:
            self.reporter.error(f"Failed to start bridge: {e}", context="BridgeManager")
            return False

    def stop(self) -> None:
        """Stop bridge server subprocess."""
        if self.process is None:
            return

        self.reporter.info("Stopping bridge server...", context="BridgeManager")

        try:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.reporter.warning(
                    "Bridge didn't stop gracefully, forcing kill",
                    context="BridgeManager",
                )
                self.process.kill()
                self.process.wait()

            self.reporter.info("Bridge server stopped", context="BridgeManager")

        except Exception as e:
            self.reporter.error(f"Error stopping bridge: {e}", context="BridgeManager")

        finally:
            self.process = None

    def _is_ready(self) -> bool:
        """
        Check if bridge server is ready.

        Returns:
            True if health endpoint responds, False otherwise
        """
        try:
            response = requests.get(f"{self.bridge_url}/health", timeout=2)
            ready = response.status_code == 200
            if not ready:
                self.reporter.warning(
                    f"Health check returned status {response.status_code}",
                    context="BridgeManager",
                )
            return ready
        except requests.exceptions.RequestException:
            return False

    def is_running(self) -> bool:
        """
        Check if bridge server is running.

        Returns:
            True if running, False otherwise
        """
        return self.process is not None and self.process.poll() is None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.stop()
