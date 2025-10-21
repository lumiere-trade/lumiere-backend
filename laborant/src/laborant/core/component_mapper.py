"""
Component mapper - maps changed files to components and their tests.

Discovers components based on directory structure and finds their tests.
"""

from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Set

from shared.reporter.system_reporter import SystemReporter


class ComponentMapper:
    """
    Maps changed files to components and discovers their tests.

    Convention:
    - Component = first-level directory with tests/ subdirectory
    - Test structure: component/tests/{unit,integration,e2e}/test_*.py
    """

    def __init__(self, project_root: Path, reporter: Optional[SystemReporter] = None):
        """
        Initialize component mapper.

        Args:
            project_root: Root directory of project
            reporter: Optional reporter for logging
        """
        self.project_root = project_root
        self.reporter = reporter or SystemReporter(
            name="component_mapper", level=20, verbose=1
        )

    def extract_component_names(self, files: List[Path]) -> Set[str]:
        """
        Extract unique component names from file paths.

        Component = first-level directory name.

        Args:
            files: List of changed file paths

        Returns:
            Set of component names
        """
        components = set()

        for file_path in files:
            try:
                relative = file_path.relative_to(self.project_root)
                parts = relative.parts

                if len(parts) > 0:
                    component_name = parts[0]
                    components.add(component_name)

            except ValueError:
                # File is outside project root
                continue

        return components

    def has_tests(self, component_name: str) -> bool:
        """
        Check if component has tests directory.

        Args:
            component_name: Name of component

        Returns:
            True if component has tests/ directory
        """
        component_path = self.project_root / component_name
        tests_path = component_path / "tests"

        return tests_path.exists() and tests_path.is_dir()

    def discover_test_files(
        self,
        component_name: str,
        categories: Optional[List[str]] = None,
        file_pattern: Optional[str] = None,
    ) -> Dict[str, List[Path]]:
        """
        Discover test files for a component.

        Args:
            component_name: Name of component
            categories: Optional list of categories to include
                       (e.g., ["unit", "integration"])
                       If None, discovers all categories
            file_pattern: Optional file pattern to filter results
                         (e.g., "test_escrow*.py")

        Returns:
            Dict mapping category to list of test files
            Example: {"unit": [Path(...), ...], "integration": [...]}
        """
        if categories is None:
            categories = ["unit", "integration", "e2e"]

        tests_path = self.project_root / component_name / "tests"

        if not tests_path.exists():
            self.reporter.warning(
                f"No tests directory for {component_name}", context="ComponentMapper"
            )
            return {}

        discovered = {}

        for category in categories:
            category_path = tests_path / category

            if not category_path.exists():
                continue

            # Find all test_*.py files RECURSIVELY
            test_files = sorted(category_path.rglob("test_*.py"))

            # Apply file pattern filter if provided
            if file_pattern:
                test_files = [
                    f for f in test_files if fnmatch(f.name, file_pattern)
                ]

            if test_files:
                discovered[category] = test_files

        return discovered

    def discover_all_components(self) -> List[str]:
        """
        Discover all components in project.

        A component is a first-level directory with tests/ subdirectory.

        Returns:
            List of component names
        """
        components = []

        for item in self.project_root.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden directories
            if item.name.startswith("."):
                continue

            # Skip common non-component directories
            if item.name in [
                "node_modules",
                "venv",
                "venv311",
                "__pycache__",
                "logs",
                "docs",
                "scripts",
                "build",
                "dist",
            ]:
                continue

            # Check if has tests directory
            if self.has_tests(item.name):
                components.append(item.name)

        self.reporter.info(
            f"Discovered {len(components)} component(s) with tests",
            context="ComponentMapper",
        )

        return sorted(components)

    def validate_component_structure(self, component_name: str) -> Dict[str, bool]:
        """
        Validate component test structure.

        Checks for expected directories and files.

        Args:
            component_name: Name of component

        Returns:
            Dict with validation results
        """
        component_path = self.project_root / component_name
        tests_path = component_path / "tests"

        validation = {
            "exists": component_path.exists(),
            "has_tests_dir": tests_path.exists(),
            "has_unit": (tests_path / "unit").exists(),
            "has_integration": (tests_path / "integration").exists(),
            "has_e2e": (tests_path / "e2e").exists(),
            "has_test_files": False,
        }

        # Check for any test files
        if tests_path.exists():
            test_files = list(tests_path.rglob("test_*.py"))
            validation["has_test_files"] = len(test_files) > 0

        return validation

    def get_component_summary(self, component_name: str) -> Dict[str, any]:
        """
        Get summary information about a component.

        Args:
            component_name: Name of component

        Returns:
            Dict with component information
        """
        validation = self.validate_component_structure(component_name)
        test_files = self.discover_test_files(component_name)

        return {
            "name": component_name,
            "exists": validation["exists"],
            "has_tests": validation["has_tests_dir"],
            "categories": list(test_files.keys()),
            "total_test_files": sum(len(files) for files in test_files.values()),
            "test_files_by_category": {
                cat: len(files) for cat, files in test_files.items()
            },
        }
