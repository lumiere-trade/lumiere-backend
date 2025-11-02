"""
Docker container management for integration and E2E tests.

Smart detection: check if containers already running before starting.
Track who started them for proper cleanup decision.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Literal, Optional

import httpx
import yaml

LUMIERE_ROOT = Path(__file__).parent.parent.parent.resolve()
COMPOSE_FILE = LUMIERE_ROOT / "docker-compose.test.yaml"
PORTS_FILE = LUMIERE_ROOT / "ports.yaml"

ProfileType = Literal["integration", "e2e"]

_started_by_us = False


class DockerComposeError(Exception):
    """Raised when docker-compose command fails."""


class TestInfrastructure:
    """Test infrastructure configuration from ports.yaml."""

    _config: Optional[Dict] = None

    @classmethod
    def load_config(cls) -> Dict:
        """Load port configuration from ports.yaml."""
        if cls._config is not None:
            return cls._config

        if not PORTS_FILE.exists():
            raise FileNotFoundError(f"ports.yaml not found at {PORTS_FILE}")

        with open(PORTS_FILE, "r") as f:
            ports_config = yaml.safe_load(f)

        test_env = ports_config["environments"]["test"]
        health_eps = ports_config["health_endpoints"]

        cls._config = {
            "ports": {
                "postgres": test_env["postgres"]["port"],
                "pourtier": test_env["pourtier"]["port"],
                "courier": test_env["courier"]["port"],
                "passeur": test_env["passeur"]["port"],
            },
            "health_endpoints": {
                "pourtier": f"http://localhost:{test_env['pourtier']['port']}{health_eps['pourtier']}",
                "courier": f"http://localhost:{test_env['courier']['port']}{health_eps['courier']}",
                "passeur": f"http://localhost:{test_env['passeur']['port']}{health_eps['passeur']}",
            },
            "service_urls": ports_config["service_discovery"]["test"],
        }

        return cls._config

    @classmethod
    def get_port(cls, service: str) -> int:
        """Get test port for service."""
        config = cls.load_config()
        return config["ports"][service]

    @classmethod
    def get_health_url(cls, service: str) -> str:
        """Get health check URL for service."""
        config = cls.load_config()
        return config["health_endpoints"][service]


def run_compose_command(
    command: List[str],
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run docker-compose command."""
    full_command = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
    ] + command

    try:
        result = subprocess.run(
            full_command,
            cwd=LUMIERE_ROOT,
            capture_output=capture_output,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        raise DockerComposeError(
            f"Docker compose failed: {' '.join(full_command)}\n"
            f"Exit code: {e.returncode}\n"
            f"Stderr: {e.stderr}"
        ) from e


async def check_service_health(service: str, timeout: float = 2.0) -> bool:
    """
    Check if a single service is healthy.

    Args:
        service: Service name
        timeout: HTTP request timeout

    Returns:
        True if healthy, False otherwise
    """
    try:
        health_url = TestInfrastructure.get_health_url(service)
        async with httpx.AsyncClient() as client:
            response = await client.get(health_url, timeout=timeout)
            return response.status_code == 200
    except Exception:
        # Any exception means not healthy (connection refused, timeout, etc.)
        return False


async def check_services_running(services: List[str]) -> bool:
    """
    Check if all services are running and healthy.

    Args:
        services: List of service names to check

    Returns:
        True if all services healthy, False otherwise
    """
    for service in services:
        if not await check_service_health(service, timeout=2.0):
            return False
    return True


async def wait_for_health(
    services: List[str],
    timeout: int = 60,
    interval: int = 2,
) -> None:
    """
    Wait for all services to be healthy.

    Args:
        services: List of service names to wait for
        timeout: Maximum seconds to wait
        interval: Seconds between checks

    Raises:
        TimeoutError: If services don't become healthy within timeout
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time

        if elapsed > timeout:
            # Get logs for debugging
            logs_info = []
            for service in services:
                try:
                    logs = get_service_logs(service, lines=20)
                    logs_info.append(f"\n{service} logs:\n{logs}")
                except Exception:
                    pass

            raise TimeoutError(
                f"Services {services} not healthy within {timeout}s"
                f"{''.join(logs_info)}"
            )

        # Check all services
        all_healthy = True
        for service in services:
            if not await check_service_health(service, timeout=3.0):
                all_healthy = False
                break

        if all_healthy:
            return

        await asyncio.sleep(interval)


async def ensure_test_containers(
    profile: ProfileType,
    timeout: int = 60,
) -> None:
    """
    Ensure test containers are running (smart detection).

    Only starts containers if not already running.
    Tracks if we started them for cleanup decision.

    Args:
        profile: "integration" (postgres + pourtier) or "e2e" (full stack)
        timeout: Maximum seconds to wait for health checks
    """
    global _started_by_us

    # Determine services
    if profile == "integration":
        services_to_check = ["pourtier"]
    else:  # e2e
        services_to_check = ["pourtier", "courier", "passeur"]

    # Check if already running
    already_running = await check_services_running(services_to_check)

    if already_running:
        _started_by_us = False
        return

    # Start containers
    run_compose_command(["--profile", profile, "up", "-d"])
    _started_by_us = True

    # Wait for health
    await wait_for_health(services_to_check, timeout=timeout)


async def cleanup_test_containers(force: bool = False) -> None:
    """
    Cleanup test containers (smart decision).

    Only stops containers if we started them, unless force=True.

    Args:
        force: If True, always stop regardless of who started
    """
    global _started_by_us

    if not force and not _started_by_us:
        return

    run_compose_command(["down", "-v", "--remove-orphans"], check=False)
    _started_by_us = False


def get_service_logs(service: str, lines: int = 50) -> str:
    """Get logs from a service."""
    result = run_compose_command(
        ["logs", "--tail", str(lines), service],
        check=False,
    )
    return result.stdout


# Convenience functions
async def start_integration_tests() -> None:
    """Start containers for integration tests."""
    await ensure_test_containers(profile="integration")


async def start_e2e_tests() -> None:
    """Start containers for E2E tests."""
    await ensure_test_containers(profile="e2e")


async def stop_test_infrastructure(force: bool = False) -> None:
    """Stop test infrastructure."""
    await cleanup_test_containers(force=force)
