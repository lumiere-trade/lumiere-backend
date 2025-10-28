"""
Docker test executor - runs tests inside Docker containers.

Manages test infrastructure lifecycle and executes tests in component-specific
test containers. Provides clean separation between orchestration and execution.

Uses component-level docker-compose-test.yaml files.
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
    Executes tests inside component-specific Docker test containers.

    Responsibilities:
    - Manage test infrastructure lifecycle (start/stop containers)
    - Execute tests in isolated Docker environment per component
    - Parse and return test results

    Uses component-level docker-compose-test.yaml files.
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
        self._infrastructure_started = False
        self._current_component = None

    def _get_compose_file_path(self, component: str) -> Optional[Path]:
        """
        Get component-level docker-compose-test.yaml file path.

        Args:
            component: Component name

        Returns:
            Path to docker-compose-test.yaml or None if doesn't exist
        """
        component_path = self.project_root / component
        compose_file = component_path / "docker-compose-test.yaml"

        if compose_file.exists():
            return compose_file

        return None

    def _get_container_name(self, component: str) -> str:
        """
        Get test container name for component.

        Args:
            component: Component name (e.g., 'pourtier', 'passeur')

        Returns:
            Container name (e.g., 'pourtier-test')
        """
        return f"{component}-test"

    def _container_exists(self, container_name: str) -> bool:
        """
        Check if container exists and is running.

        Args:
            container_name: Name of container to check

        Returns:
            True if container exists and is running
        """
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True,
            )
            return container_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def ensure_infrastructure(self, component: Optional[str] = None) -> bool:
        """
        Ensure test infrastructure is running for component.

        Uses component-level docker-compose-test.yaml if it exists.
        If component has no docker-compose file, returns True (no infrastructure needed).

        Args:
            component: Component name (required)

        Returns:
            True if infrastructure is ready or not needed
        """
        if not component:
            self.reporter.error(
                "Component name required for Docker infrastructure",
                context="DockerTestExecutor",
            )
            return False

        # If infrastructure already started for this component, reuse it
        if self._infrastructure_started and self._current_component == component:
            self.reporter.debug(
                f"Infrastructure already started for {component}",
                context="DockerTestExecutor",
            )
            return True

        # Get component-level compose file
        compose_file = self._get_compose_file_path(component)

        if not compose_file:
            self.reporter.info(
                f"No docker-compose-test.yaml found for {component} - will run tests on host",
                context="DockerTestExecutor",
            )
            # No infrastructure needed - component runs on host
            return True

        self.reporter.info(
            f"Starting test infrastructure for {component}...",
            context="DockerTestExecutor",
        )

        try:
            # Check if container already running
            container_name = self._get_container_name(component)
            if self._container_exists(container_name):
                self.reporter.info(
                    f"Test infrastructure for {component} already running",
                    context="DockerTestExecutor",
                )
                self._infrastructure_started = True
                self._current_component = component
                return True

            # Start infrastructure from component directory
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    "docker-compose-test.yaml",
                    "up",
                    "-d",
                ],
                cwd=str(compose_file.parent),  # Run from component directory
                capture_output=True,
                text=True,
                check=True,
            )

            self.reporter.info(
                f"Test infrastructure for {component} started successfully",
                context="DockerTestExecutor",
            )
            self._infrastructure_started = True
            self._current_component = component

            # Wait for services to be ready
            time.sleep(5)

            return True

        except subprocess.CalledProcessError as e:
            self.reporter.error(
                f"Failed to start infrastructure for {component}: {e.stderr}",
                context="DockerTestExecutor",
            )
            return False

    def cleanup_infrastructure(
        self, component: Optional[str] = None, force: bool = False
    ) -> None:
        """
        Stop test infrastructure for component.

        Args:
            component: Component name (if None, uses current component)
            force: If True, always stop. If False, only stop if we started it.
        """
        if not force and not self._infrastructure_started:
            self.reporter.debug(
                "Skipping cleanup (infrastructure not started by us)",
                context="DockerTestExecutor",
            )
            return

        component = component or self._current_component
        if not component:
            self.reporter.warning(
                "No component specified for cleanup", context="DockerTestExecutor"
            )
            return

        compose_file = self._get_compose_file_path(component)
        if not compose_file:
            # No infrastructure to clean up
            return

        self.reporter.info(
            f"Stopping test infrastructure for {component}...",
            context="DockerTestExecutor",
        )

        try:
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    "docker-compose-test.yaml",
                    "down",
                    "-v",
                ],
                cwd=str(compose_file.parent),  # Run from component directory
                capture_output=True,
                text=True,
                check=True,
            )

            self.reporter.info(
                f"Test infrastructure for {component} stopped",
                context="DockerTestExecutor",
            )
            self._infrastructure_started = False
            self._current_component = None

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
            test_file: Path to test file
            component: Component name
            category: Test category (unit/integration/e2e)

        Returns:
            TestFileResult with execution results
        """
        if not self.can_execute(test_file):
            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error="Test file cannot be executed",
                stderr="",
                duration=0.0,
            )

        # Ensure infrastructure is running for this component
        if not self.ensure_infrastructure(component):
            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error="Failed to start test infrastructure",
                stderr="",
                duration=0.0,
            )

        # Check if component has docker-compose (if not, shouldn't be here)
        compose_file = self._get_compose_file_path(component)
        if not compose_file:
            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Component {component} has no docker-compose-test.yaml - should run on host",
                stderr="",
                duration=0.0,
            )

        container_name = self._get_container_name(component)

        # Verify container is running
        if not self._container_exists(container_name):
            return self._create_error_result(
                test_file=test_file,
                component=component,
                category=category,
                error=f"Container {container_name} not running",
                stderr="",
                duration=0.0,
            )

        # Get relative path for test file
        try:
            relative_path = test_file.relative_to(self.project_root / component)
        except ValueError:
            relative_path = test_file

        self.reporter.debug(
            f"Executing {relative_path} in {container_name}",
            context="DockerTestExecutor",
        )

        start_time = time.time()

        try:
            # Execute test in container using unittest (not pytest)
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    container_name,
                    "python",
                    str(relative_path),
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            # Parse JSON output
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

        Infrastructure is started once per component and reused for all tests.

        Args:
            test_files: List of (test_file_path, component, category) tuples

        Returns:
            List of TestFileResult objects
        """
        results = []

        # Group tests by component
        tests_by_component = {}
        for test_file, component, category in test_files:
            if component not in tests_by_component:
                tests_by_component[component] = []
            tests_by_component[component].append((test_file, component, category))

        # Execute tests component by component
        for component, component_tests in tests_by_component.items():
            if not self.ensure_infrastructure(component):
                self.reporter.error(
                    f"Failed to start infrastructure for {component}",
                    context="DockerTestExecutor",
                )
                # Create error results for all tests in this component
                for test_file, comp, category in component_tests:
                    results.append(
                        self._create_error_result(
                            test_file=test_file,
                            component=comp,
                            category=category,
                            error="Failed to start infrastructure",
                            stderr="",
                            duration=0.0,
                        )
                    )
                continue

            # Execute all tests for this component
            for test_file, comp, category in component_tests:
                result = self.execute_test_file(test_file, comp, category)
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
