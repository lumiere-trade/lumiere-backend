"""
Bridge management commands.
"""

import subprocess
import time
from pathlib import Path

import requests
import yaml


def load_config(config_file: str) -> dict:
    """Load configuration file."""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


def get_bridge_url(config: dict) -> str:
    """Get bridge URL from config."""
    host = config.get("bridge_host", "127.0.0.1")
    port = config.get("bridge_port", 8767)
    return f"http://{host}:{port}"


def check_bridge_status() -> tuple[bool, str]:
    """
    Check if bridge is running.

    Returns:
        Tuple of (is_running, url)
    """
    # Load config to get the correct URL
    try:
        import os
        env = os.getenv("ENV", "development")
        config_map = {
            "production": "production.yaml",
            "development": "development.yaml",
        }
        config_file = config_map.get(env, "development.yaml")
        config = load_config(config_file)
        url = get_bridge_url(config)
    except Exception:
        # Fallback to default development URL
        url = "http://127.0.0.1:8767"

    try:
        response = requests.get(f"{url}/health", timeout=2)
        return response.status_code == 200, url
    except BaseException:
        return False, url


def start_bridge(config_file: str) -> bool:
    """
    Start the bridge server.

    Args:
        config_file: Config file name

    Returns:
        True if successful
    """
    # Check if already running
    is_running, _ = check_bridge_status()
    if is_running:
        print("⚠️  Bridge is already running")
        return True

    # Get bridge directory
    bridge_dir = Path(__file__).parent.parent.parent.parent / "bridge"

    if not bridge_dir.exists():
        print(f"❌ Bridge directory not found: {bridge_dir}")
        return False

    try:
        # Start bridge in background
        subprocess.Popen(
            ["node", "server.js"],
            cwd=str(bridge_dir),
            env={**subprocess.os.environ, "PASSEUR_CONFIG": config_file},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for bridge to be ready
        for _ in range(10):
            time.sleep(1)
            is_running, _ = check_bridge_status()
            if is_running:
                return True

        print("❌ Bridge failed to start (timeout)")
        return False

    except Exception as e:
        print(f"❌ Error starting bridge: {e}")
        return False


def stop_bridge() -> bool:
    """
    Stop the bridge server.

    Returns:
        True if successful
    """
    try:
        # Kill node server process
        subprocess.run(
            ["pkill", "-f", "node.*server.js"],
            check=False,
            capture_output=True,
        )

        # Wait a bit
        time.sleep(1)

        # Check if stopped
        is_running, _ = check_bridge_status()

        if is_running:
            print("⚠️  Bridge may still be running")
            return False

        return True

    except Exception as e:
        print(f"❌ Error stopping bridge: {e}")
        return False
