"""
Docker container management for integration and E2E tests.

Provides utilities to start, stop, and manage Docker Compose test infrastructure.
Uses docker-compose.test.yaml with profiles (integration, e2e).

All port configuration read from ports.yaml (Single Source of Truth).

Usage in tests:
    from shared.tests.docker_helper import start_test_containers, stop_test_containers
    
    async def async_setup(self):
        await start_test_containers(profile="integration")
    
    async def async_teardown(self):
        await stop_test_containers()
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Literal, Optional

import httpx
import yaml

# Path to lumiere-public root
LUMIERE_ROOT = Path(__file__).parent.parent.parent.resolve()
COMPOSE_FILE = LUMIERE_ROOT / "docker-compose.test.yaml"
PORTS_FILE = LUMIERE_ROOT / "ports.yaml"

ProfileType = Literal["integration", "e2e"]


class DockerComposeError(Exception):
    """Raised when docker-compose command fails."""


class TestInfrastructure:
    """Test infrastructure configuration from ports.yaml."""

    _config: Optional[Dict] = None

    @classmethod
    def load_config(cls) -> Dict:
        """
        Load port configuration from ports.yaml.
        
        Returns:
            Dict with test environment ports and health endpoints
        """
        if cls._config is not None:
            return cls._config

        if not PORTS_FILE.exists():
            raise FileNotFoundError(f"ports.yaml not found at {PORTS_FILE}")

        with open(PORTS_FILE, "r") as f:
            ports_config = yaml.safe_load(f)

        # Extract test environment config
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
    """
    Run docker-compose command.

    Args:
        command: Command arguments (e.g., ["up", "-d", "--profile", "integration"])
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr

    Returns:
        CompletedProcess instance

    Raises:
        DockerComposeError: If command fails and check=True
    """
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
            f"Stdout: {e.stdout}\n"
            f"Stderr: {e.stderr}"
        ) from e


async def wait_for_health(
    services: List[str],
    timeout: int = 60,
    interval: int = 2,
) -> None:
    """
    Wait for services to be healthy.

    Args:
        services: List of service names to wait for
        timeout: Maximum seconds to wait
        interval: Seconds between health checks

    Raises:
        TimeoutError: If services don't become healthy within timeout
    """
    start_time = asyncio.get_event_loop().time()

    async with httpx.AsyncClient() as client:
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed > timeout:
                raise TimeoutError(
                    f"Services {services} did not become healthy within {timeout}s"
                )

            all_healthy = True
            
            for service in services:
                try:
                    health_url = TestInfrastructure.get_health_url(service)
                    response = await client.get(health_url, timeout=5.0)
                    
                    if response.status_code != 200:
                        all_healthy = False
                        break
                        
                except (httpx.ConnectError, httpx.TimeoutException):
                    all_healthy = False
                    break

            if all_healthy:
                return

            await asyncio.sleep(interval)


async def start_test_containers(
    profile: ProfileType,
    pull: bool = False,
    build: bool = False,
    timeout: int = 60,
) -> None:
    """
    Start test containers using docker-compose profiles.

    Args:
        profile: "integration" (postgres + pourtier) or "e2e" (full stack)
        pull: Pull latest images before starting
        build: Rebuild images before starting
        timeout: Maximum seconds to wait for health checks

    Raises:
        DockerComposeError: If containers fail to start or become healthy
    """
    # Pull images if requested
    if pull:
        run_compose_command(["--profile", profile, "pull"])

    # Build images if requested
    if build:
        run_compose_command(["--profile", profile, "build"])

    # Start containers
    run_compose_command(["--profile", profile, "up", "-d"])

    # Determine which services to wait for
    if profile == "integration":
        services_to_wait = ["pourtier"]
    else:  # e2e
        services_to_wait = ["pourtier", "courier", "passeur"]

    # Wait for services to be healthy
    await wait_for_health(services_to_wait, timeout=timeout)


async def stop_test_containers(
    remove_volumes: bool = True,
    remove_orphans: bool = True,
) -> None:
    """
    Stop and cleanup test containers.

    Args:
        remove_volumes: Remove named volumes (cleans test data)
        remove_orphans: Remove containers not in compose file
    """
    command = ["down"]

    if remove_volumes:
        command.append("-v")

    if remove_orphans:
        command.append("--remove-orphans")

    run_compose_command(command, check=False)


def get_service_logs(service: str, lines: int = 50) -> str:
    """
    Get logs from a service.

    Args:
        service: Service name
        lines: Number of lines to retrieve

    Returns:
        Log output as string
    """
    result = run_compose_command(
        ["logs", "--tail", str(lines), service],
        check=False,
    )
    return result.stdout
