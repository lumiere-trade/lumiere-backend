"""
Laborant orchestrator - main coordinator for test execution.

Coordinates:
- Change detection (git diff)
- Component mapping (files → components)
- Test execution (run tests)
- Result aggregation (collect results)
- Reporting (display results)
- Commit decision (block/allow)
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console
from shared.reporter.emojis import LaborantEmoji
from shared.reporter.system_reporter import SystemReporter
from shared.tests.models import TestFileResult

from laborant.core.change_detector import ChangeDetector
from laborant.core.component_mapper import ComponentMapper
from laborant.core.docker_test_executor import DockerTestExecutor
from laborant.core.reporter import LaborantReporter
from laborant.core.test_executor import TestExecutor


@dataclass
class ComponentTestResult:
    """
    Aggregated test results for one component.
    """

    component_name: str
    category_results: Dict[str, List[TestFileResult]] = field(default_factory=dict)
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_errors: int = 0
    total_duration: float = 0.0
    has_tests: bool = True

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.total_failed == 0 and self.total_errors == 0

    def add_result(self, category: str, result: TestFileResult):
        """Add a test file result to this component."""
        if category not in self.category_results:
            self.category_results[category] = []

        self.category_results[category].append(result)

        # Update totals
        self.total_tests += result.total
        self.total_passed += result.passed
        self.total_failed += result.failed
        self.total_errors += result.errors
        self.total_duration += result.duration


class Laborant:
    """
    Main orchestrator for Laborant test runner.

    Coordinates all components to detect changes, map to tests,
    execute tests, and report results.

    Uses:
    - TestExecutor for unit tests (fast, local execution)
    - DockerTestExecutor for integration/e2e tests (Docker environment)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        verbose: bool = False,
        timeout: int = 120,
        fail_fast: bool = False,
    ):
        """
        Initialize Laborant orchestrator.

        Args:
            project_root: Project root directory (default: cwd)
            verbose: Enable verbose output
            timeout: Test timeout in seconds
            fail_fast: Stop on first failure
        """
        self.project_root = project_root or Path.cwd()
        self.verbose = verbose
        self.timeout = timeout
        self.fail_fast = fail_fast

        # Initialize reporter for logging
        self.reporter = SystemReporter(
            name="laborant",
            log_dir="logs",
            level=10 if verbose else 20,
            verbose=2 if verbose else 1,
        )

        # Initialize components
        self.change_detector = ChangeDetector(self.project_root, self.reporter)
        self.component_mapper = ComponentMapper(self.project_root, self.reporter)

        # Initialize executors
        self.test_executor = TestExecutor(self.project_root, timeout, self.reporter)
        self.docker_executor = DockerTestExecutor(
            self.project_root, timeout, self.reporter
        )

        # Initialize display reporter and Rich console
        self.display_reporter = LaborantReporter()
        self.console = Console()

        # Results tracking
        self.component_results: Dict[str, ComponentTestResult] = {}
        self.components_without_tests: List[str] = []

    def run(
        self,
        components: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        skip_git: bool = False,
        file_pattern: Optional[str] = None,
    ) -> bool:
        """
        Run Laborant test orchestration.

        Args:
            components: Specific components to test (None = auto-detect)
            categories: Test categories to run (None = all)
            skip_git: Skip git detection, use provided components
            file_pattern: File pattern to filter test files (e.g., test_*.py)

        Returns:
            True if all tests passed, False otherwise
        """
        start_time = time.time()

        self.reporter.info("=" * 67, context="Laborant")
        self.reporter.info(
            f"{LaborantEmoji.TEST_RUN} Laborant Test Runner Starting",
            context="Laborant",
        )
        self.reporter.info("=" * 67, context="Laborant")

        # Determine which components to test
        if components:
            # Manual mode - explicit components
            target_components = set(components)
            self.reporter.info(
                f"{LaborantEmoji.MANUAL} Manual mode: "
                f"{len(target_components)} component(s)",
                context="Laborant",
            )
        elif skip_git:
            # All components mode
            target_components = set(self.component_mapper.discover_all_components())
            self.reporter.info(
                f"{LaborantEmoji.DISCOVER} All components mode: "
                f"{len(target_components)} component(s)",
                context="Laborant",
            )
        else:
            # Auto mode - git detection
            target_components = self._detect_changed_components()

            if not target_components:
                self.reporter.info(
                    f"{LaborantEmoji.INFO} No changed components detected",
                    context="Laborant",
                )
                self.reporter.info(
                    f"{LaborantEmoji.SUCCESS} No tests to run - " f"Commit allowed",
                    context="Laborant",
                )
                return True

        # Run tests for each component
        all_passed = True

        for component in sorted(target_components):
            success = self._run_component_tests(
                component, categories, file_pattern=file_pattern
            )

            if not success:
                all_passed = False

                if self.fail_fast:
                    self.reporter.error(
                        f"{LaborantEmoji.STOPPED} Fail-fast enabled - " f"stopping",
                        context="Laborant",
                    )
                    break

        # Cleanup Docker infrastructure if we used it
        self.docker_executor.cleanup_infrastructure()

        # Print final summary
        total_duration = time.time() - start_time
        self._print_final_summary(total_duration)

        return all_passed

    def _detect_changed_components(self) -> Set[str]:
        """
        Detect changed components via git.

        Returns:
            Set of component names
        """
        self.reporter.info(
            f"{LaborantEmoji.AUTO} Auto mode: Detecting changes via git",
            context="Laborant",
        )

        # Check if git repository
        if not self.change_detector.is_git_repository():
            self.reporter.warning(
                f"{LaborantEmoji.WARNING} Not a git repository - "
                f"running all components",
                context="Laborant",
            )
            return set(self.component_mapper.discover_all_components())

        # Get staged files
        staged_files = self.change_detector.get_staged_files()

        if not staged_files:
            self.reporter.info(
                f"{LaborantEmoji.INFO} No staged files detected", context="Laborant"
            )
            return set()

        # Filter relevant files
        relevant_files = self.change_detector.filter_relevant_files(staged_files)

        if not relevant_files:
            self.reporter.info(
                f"{LaborantEmoji.INFO} No relevant code changes detected",
                context="Laborant",
            )
            return set()

        # Extract component names
        components = self.component_mapper.extract_component_names(relevant_files)

        return components

    def _get_executor_for_category(self, category: str):
        """
        Get appropriate executor for test category.

        Args:
            category: Test category (unit, integration, e2e)

        Returns:
            TestExecutor for unit tests, DockerTestExecutor for others
        """
        if category == "unit":
            return self.test_executor
        else:
            # integration and e2e tests run in Docker
            return self.docker_executor

    def _run_component_tests(
        self,
        component_name: str,
        categories: Optional[List[str]] = None,
        file_pattern: Optional[str] = None,
    ) -> bool:
        """
        Run all tests for a component.

        Args:
            component_name: Component name
            categories: Test categories to run (None = all)
            file_pattern: File pattern to filter test files

        Returns:
            True if all tests passed
        """
        # Check if component has tests
        if not self.component_mapper.has_tests(component_name):
            # Print header for components without tests
            header = self.display_reporter.create_component_header(
                component_name, {}  # Empty discovery - will show "No tests found!"
            )
            self.console.print(header)

            self.components_without_tests.append(component_name)

            # Create result entry
            self.component_results[component_name] = ComponentTestResult(
                component_name=component_name, has_tests=False
            )

            return True  # No tests = allow (programmer's responsibility)

        # Discover ALL tests with optional file pattern filter
        all_test_files = self.component_mapper.discover_test_files(
            component_name, categories=None, file_pattern=file_pattern
        )

        # Build test discovery summary
        test_discovery = {
            category: len(files) for category, files in all_test_files.items()
        }

        # Print component header with test discovery
        header = self.display_reporter.create_component_header(
            component_name, test_discovery
        )
        self.console.print(header)

        if not all_test_files:
            self.components_without_tests.append(component_name)
            return True

        # Initialize result tracking
        component_result = ComponentTestResult(component_name=component_name)

        # CRITICAL: Execute tests in strict order: unit → integration → e2e
        # This ensures unit tests run before integration, etc.
        test_order = ["unit", "integration", "e2e"]

        for category in test_order:
            # Skip if category doesn't exist in discovered tests
            if category not in all_test_files:
                continue

            # Skip if not in requested categories (user filter)
            if categories and category not in categories:
                continue

            # Get appropriate executor for this category
            executor = self._get_executor_for_category(category)

            # Get file count for category
            file_count = len(all_test_files[category])

            # Print category header panel
            cat_header = self.display_reporter.create_category_header_panel(
                category, file_count, component_name
            )
            self.console.print(cat_header)

            # Run each test file in category
            for test_file in all_test_files[category]:
                # Execute test with appropriate executor
                result = executor.execute_test_file(test_file, component_name, category)

                # Add to component results
                component_result.add_result(category, result)

                # Create and print test file panel with all results
                test_panel = self.display_reporter.create_test_file_panel(
                    test_file.name,
                    component_name,
                    category,
                    result.tests,
                    result.passed,
                    result.total,
                    result.duration,
                )
                self.console.print(test_panel)
                self.console.print()  # Blank line after panel

                # Print error details if failed and verbose
                if not result.success and self.verbose:
                    for test in result.tests:
                        if test.error:
                            self.reporter.error(
                                f"{LaborantEmoji.TEST_ERROR} "
                                f"{test.name}: {test.error}",
                                context="Laborant",
                            )

                # Fail-fast check
                if not result.success and self.fail_fast:
                    self.reporter.error(
                        f"{LaborantEmoji.TEST_FAIL} Test failed: " f"{test_file.name}",
                        context="Laborant",
                    )
                    self.component_results[component_name] = component_result
                    return False

            # Category done - blank line
            self.console.print()

        # Print component summary using Rich
        comp_summary = self.display_reporter.create_component_summary(
            component_name,
            component_result.category_results,
            component_result.total_tests,
            component_result.total_passed,
            component_result.total_failed,
            component_result.total_errors,
        )
        self.console.print(comp_summary)

        # Save results
        self.component_results[component_name] = component_result

        return component_result.success

    def _print_final_summary(self, total_duration: float):
        """
        Print final summary of all test results.

        Args:
            total_duration: Total execution time
        """
        # Calculate totals
        total_components = len(self.component_results)
        total_tests = sum(r.total_tests for r in self.component_results.values())
        total_passed = sum(r.total_passed for r in self.component_results.values())
        total_failed = sum(r.total_failed for r in self.component_results.values())
        total_errors = sum(r.total_errors for r in self.component_results.values())

        # Build category breakdown
        category_breakdown = {}
        category_order = ["unit", "integration", "e2e"]

        for category in category_order:
            cat_total = 0
            cat_passed = 0
            cat_failed = 0

            for result in self.component_results.values():
                if category in result.category_results:
                    for test_result in result.category_results[category]:
                        cat_total += test_result.total
                        cat_passed += test_result.passed
                        cat_failed += test_result.failed + test_result.errors

            if cat_total > 0:
                category_breakdown[category] = {
                    "total": cat_total,
                    "passed": cat_passed,
                    "failed": cat_failed,
                }

        # Components with failures
        components_with_failures = [
            name
            for name, result in self.component_results.items()
            if not result.success and result.has_tests
        ]

        # Print summary using Rich Panel
        summary = self.display_reporter.create_final_summary(
            total_components,
            total_tests,
            total_passed,
            total_failed,
            total_errors,
            total_duration,
            category_breakdown,
            components_with_failures,
            self.components_without_tests,
        )

        self.console.print(summary)
