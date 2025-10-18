"""
Docker test executor - runs tests inside Docker containers.

Manages test infrastructure lifecycle and executes tests in test-runner container.
Provides clean separation between orchestration and test execution.
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from shared.reporter.system_reporter import SystemReporter
from shared.tests.models import TestFileResult
from shared.tests.result_schema import parse_test_output, validate_test_output


class DockerTestExecutor:
    """
    Executes tests inside Docker test-runner container.

    Responsibilities:
    - Manage test infrastructure lifecycle (start/stop containers)
    - Execute tests in isolated Docker environment
    - Parse and return test results
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = 120,
        reporter: Optional[SystemReporter] = None,
    ):
        """
        Initialize Docker test executor.

        Args:
            project_root: Root directory of project
            timeout: Test timeout in seconds
            reporter: Optional reporter for logging
        """
        self.project_root = project_root
        self.timeout = timeout
        self.reporter = reporter or SystemReporter(
            name="docker_test_executor", level=20, verbose=1
        )
        self.compose_file = project_root / "docker-compose.test.yaml"
        self._infrastructure_started = False

    def ensure_infrastructure(self, profile: str = "test-runner") -> bool:
        """
        Ensure test infrastructure is running.

        Uses smart detection - only starts if not already running.

        Args:
            profile: Docker compose profile (default: test-runner)

        Returns:
            True if infrastructure is ready
        """
        if self._infrastructure_started:
            self.reporter.debug(
                "Infrastructure already started", context="DockerTestExecutor"
            )
            return True

        self.reporter.info(
            "Starting test infrastructure...", context="DockerTestExecutor"
        )

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=lumiere-test-runner",
                    "--format",
                    "{{.Names}}",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
            )

            if "lumiere-test-runner" in result.stdout:
                self.reporter.info(
                    "Test infrastructure already running", context="DockerTestExecutor"
                )
                self._infrastructure_started = True
                return True

            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "--profile",
                    profile,
                    "up",
                    "-d",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
            )

            self.reporter.info(
                "Test infrastructure started successfully", context="DockerTestExecutor"
            )
            self._infrastructure_started = True

            time.sleep(5)

            return True

        except subprocess.CalledProcessError as e:
            self.reporter.error(
                f"Failed to start infrastructure: {e.stderr}",
                context="DockerTestExecutor",
            )
            return False

    def cleanup_infrastructure(self, force: bool = False) -> None:
        """
        Stop test infrastructure.

        Args:
            force: If True, always stop. If False, only stop if we started it.
        """
        if not force and not self._infrastructure_started:
            self.reporter.debug(
                "Skipping cleanup (infrastructure not started by us)",
                context="DockerTestExecutor",
            )
            return

        self.reporter.info(
            "Stopping test infrastructure...", context="DockerTestExecutor"
        )

        try:
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "down",
                    "-v",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
            )

            self.reporter.info(
                "Test infrastructure stopped", context="DockerTestExecutor"
            )
            self._infrastructure_started = False

        except subprocess.CalledProcessError as e:
            self.reporter.error(
                f"Failed to stop infrastructure: {e.stderr}",
                context="DockerTestExecutor",
            )

    def execute_test_file(
        self, test_file: Path, component: str, category: str
    ) -> TestFileResult:
        """
        Execute a single test file in Docker container.

        Args:
            test_file: Path to test file (relative to project root)
            component: Component name
            category: Test category (unit, integration, e2e)

        Returns:
            TestFileResult with execution details
        """
        relative_path = test_file.relative_to(self.project_root)

        self.reporter.debug(
            f"Executing in container: {relative_path}", context="DockerTestExecutor"
        )

        if not self.ensure_infrastructure():
            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error="Failed to start test infrastructure",
                stderr="",
                duration=0.0,
            )

        # Construct path inside container
        # Handle both with and without subcategory
        # E2E: pourtier/tests/e2e/test_file.py -> /app/tests/e2e/test_file.py
        # Integration: pourtier/tests/integration/api/test_file.py -> /app/tests/integration/api/test_file.py
        parts = relative_path.parts
        if len(parts) == 4:
            container_path = f"/app/tests/{parts[2]}/{parts[3]}"
        else:
            container_path = f"/app/tests/{parts[2]}/{parts[3]}/{parts[4]}"

        start_time = time.time()

        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "lumiere-test-runner",
                    "python",
                    container_path,
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            test_data = parse_test_output(result.stdout)

            if test_data is None:
                return self._create_error_result(
                    test_file=test_file,
                    component=component,
                    category=category,
                    error="Failed to parse test output",
                    stderr=result.stderr,
                    duration=duration,
                )

            is_valid, error_msg = validate_test_output(test_data)

            if not is_valid:
                return self._create_error_result(
                    test_file=test_file,
                    component=component,
                    category=category,
                    error=f"Invalid test output: {error_msg}",
                    stderr=result.stderr,
                    duration=duration,
                )

            test_result = TestFileResult(**test_data)

            if test_result.success:
                self.reporter.debug(
                    f"{test_result.passed}/{test_result.total} passed ({duration:.2f}s)",
                    context="DockerTestExecutor",
                )
            else:
                self.reporter.debug(
                    f"{test_result.failed + test_result.errors} failed ({duration:.2f}s)",
                    context="DockerTestExecutor",
                )

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.reporter.error(
                f"Test timeout after {self.timeout}s", context="DockerTestExecutor"
            )

            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Test timeout after {self.timeout}s",
                stderr="",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            self.reporter.error(f"Execution error: {e}", context="DockerTestExecutor")

            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Execution error: {str(e)}",
                stderr="",
                duration=duration,
            )

    def execute_test_files(
        self, test_files: List[tuple[Path, str, str]]
    ) -> List[TestFileResult]:
        """
        Execute multiple test files in batch mode.

        Infrastructure is started once and reused for all tests.

        Args:
            test_files: List of (test_file_path, component, category) tuples

        Returns:
            List of TestFileResult objects
        """
        results = []

        if not self.ensure_infrastructure():
            self.reporter.error(
                "Failed to start infrastructure for batch execution",
                context="DockerTestExecutor",
            )
            return results

        for test_file, component, category in test_files:
            result = self.execute_test_file(test_file, component, category)
            results.append(result)

        return results

    def _create_error_result(
        self,
        test_file: Path,
        component: str,
        category: str,
        error: str,
        stderr: str,
        duration: float,
    ) -> TestFileResult:
        """Create error result when test execution fails."""
        from shared.tests.models import IndividualTestResult
        from shared.tests.result_schema import SCHEMA_VERSION

        error_details = error
        if stderr:
            error_details += f"\n\nStderr:\n{stderr[:500]}"

        return TestFileResult(
            schema_version=SCHEMA_VERSION,
            test_file=test_file.name,
            component=component,
            category=category,
            total=1,
            passed=0,
            failed=0,
            errors=1,
            skipped=0,
            duration=duration,
            timestamp=datetime.now().isoformat(),
            tests=[
                IndividualTestResult(
                    name="execution_error",
                    status="error",
                    duration=duration,
                    error=error_details,
                )
            ],
            metadata={
                "error_type": "execution_failure",
                "test_file": str(test_file),
                "execution_mode": "docker",
            },
        )

    def can_execute(self, test_file: Path) -> bool:
        """Check if test file can be executed."""
        if not test_file.exists():
            self.reporter.error(
                f"Test file does not exist: {test_file}",
                context="DockerTestExecutor",
            )
            return False

        if test_file.suffix != ".py":
            self.reporter.error(
                f"Test file is not Python: {test_file}",
                context="DockerTestExecutor",
            )
            return False

        return True
