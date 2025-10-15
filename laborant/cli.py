"""
Laborant CLI - Command-line interface for test orchestration.

Provides commands for:
- Auto mode (git detection)
- Manual mode (specific components)
- All components mode
- Dry run
- List components
- Install git pre-commit hook
- Code quality checks (lint, format)

All output via SystemReporter with LaborantEmoji.
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from shared.reporter.emojis import LaborantEmoji, SystemEmoji
from shared.reporter.system_reporter import SystemReporter

from laborant.core.change_detector import ChangeDetector
from laborant.core.component_mapper import ComponentMapper
from laborant.core.orchestrator import Laborant


def install_hook(project_root: Path, reporter: SystemReporter) -> int:
    """
    Install git pre-commit hook.

    Args:
        project_root: Project root directory
        reporter: SystemReporter instance

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    reporter.info("", context="CLI")
    reporter.info(
        f"{SystemEmoji.BUILD} Installing Laborant pre-commit hook", context="CLI"
    )
    reporter.info("", context="CLI")

    # Check if git repository
    git_dir = project_root / ".git"
    if not git_dir.exists():
        reporter.error(
            f"{LaborantEmoji.TEST_ERROR} Not a git repository", context="CLI"
        )
        reporter.info(
            f"{LaborantEmoji.INFO} Run this command from project root", context="CLI"
        )
        reporter.info("", context="CLI")
        return 1

    # Check if hooks directory exists
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Pre-commit hook path
    hook_path = hooks_dir / "pre-commit"

    # Check if hook already exists
    if hook_path.exists():
        reporter.warning(
            f"{LaborantEmoji.WARNING} Pre-commit hook already exists", context="CLI"
        )
        reporter.info(f"{LaborantEmoji.INFO} Location: {hook_path}", context="CLI")
        reporter.info("", context="CLI")

        # Ask for confirmation (read from stdin)
        reporter.info(
            f"{LaborantEmoji.WARNING} Overwrite existing hook? (y/N): ", context="CLI"
        )

        try:
            response = input().strip().lower()
            if response not in ["y", "yes"]:
                reporter.info(
                    f"{LaborantEmoji.INFO} Installation cancelled", context="CLI"
                )
                reporter.info("", context="CLI")
                return 0
        except (EOFError, KeyboardInterrupt):
            reporter.info(
                f"\n{LaborantEmoji.INFO} Installation cancelled", context="CLI"
            )
            reporter.info("", context="CLI")
            return 0

        reporter.info("", context="CLI")

    # Find template file
    laborant_root = Path(__file__).parent
    template_path = laborant_root / "hooks" / "pre-commit.template"

    if not template_path.exists():
        reporter.error(
            f"{LaborantEmoji.TEST_ERROR} Hook template not found", context="CLI"
        )
        reporter.error(f"{LaborantEmoji.INFO} Expected: {template_path}", context="CLI")
        reporter.info("", context="CLI")
        return 1

    # Copy template to hooks directory
    try:
        shutil.copy(template_path, hook_path)

        # Make executable
        hook_path.chmod(0o755)

        reporter.info(
            f"{LaborantEmoji.SUCCESS} Pre-commit hook installed successfully",
            context="CLI",
        )
        reporter.info(f"{LaborantEmoji.INFO} Location: {hook_path}", context="CLI")
        reporter.info("", context="CLI")
        reporter.info(
            f"{LaborantEmoji.INFO} The hook will run automatically "
            f"before each commit",
            context="CLI",
        )
        reporter.info(
            f"{LaborantEmoji.INFO} To skip: git commit --no-verify", context="CLI"
        )
        reporter.info("", context="CLI")

        return 0

    except Exception as e:
        reporter.error(
            f"{LaborantEmoji.TEST_ERROR} Failed to install hook: {e}", context="CLI"
        )
        reporter.info("", context="CLI")
        return 1


def list_components(project_root: Path, reporter: SystemReporter) -> int:
    """
    List all available components.

    Args:
        project_root: Project root directory
        reporter: SystemReporter instance

    Returns:
        Exit code (0)
    """
    mapper = ComponentMapper(project_root, reporter)
    components = mapper.discover_all_components()

    reporter.info("", context="CLI")
    reporter.info(f"{LaborantEmoji.TEST_RUN} Available components:", context="CLI")
    reporter.info("", context="CLI")

    if not components:
        reporter.info(
            f"{LaborantEmoji.INFO} No components with tests found.", context="CLI"
        )
        reporter.info("", context="CLI")
        return 0

    for component in components:
        summary = mapper.get_component_summary(component)

        # Check if has tests
        if summary["has_tests"]:
            categories = ", ".join(summary["categories"])
            total = summary["total_test_files"]
            reporter.info(
                f"  {LaborantEmoji.COMPONENT} {component:20s} "
                f"(has tests: {categories})",
                context="CLI",
            )
            reporter.info(f"    {' ' * 20}   {total} test file(s)", context="CLI")
        else:
            reporter.warning(
                f"  {LaborantEmoji.NO_TESTS} {component:20s} " f"(no tests found)",
                context="CLI",
            )

    reporter.info("", context="CLI")
    reporter.info(
        f"{LaborantEmoji.SUMMARY} Total: {len(components)} component(s)", context="CLI"
    )
    reporter.info("", context="CLI")

    return 0


def dry_run(
    project_root: Path,
    components: list,
    skip_git: bool,
    categories: list,
    reporter: SystemReporter,
) -> int:
    """
    Dry run - show what would be executed.

    Args:
        project_root: Project root directory
        components: Component names (or None for auto)
        skip_git: Skip git detection
        categories: Test categories to run
        reporter: SystemReporter instance

    Returns:
        Exit code (0)
    """
    reporter.info("", context="CLI")
    reporter.info(
        f"{LaborantEmoji.DRY_RUN} Laborant (Dry run - no execution)", context="CLI"
    )
    reporter.info("", context="CLI")

    # Determine components
    if components:
        target_components = components
        reporter.info(
            f"{LaborantEmoji.MANUAL} Manual mode: "
            f"{len(target_components)} component(s)",
            context="CLI",
        )
        reporter.info("", context="CLI")
    elif skip_git:
        mapper = ComponentMapper(project_root, reporter)
        target_components = mapper.discover_all_components()
        reporter.info(
            f"{LaborantEmoji.DISCOVER} All components mode: "
            f"{len(target_components)} component(s)",
            context="CLI",
        )
        reporter.info("", context="CLI")
    else:
        # Auto detect via git
        detector = ChangeDetector(project_root, reporter)

        if not detector.is_git_repository():
            reporter.warning(
                f"{LaborantEmoji.WARNING} Not a git repository", context="CLI"
            )
            reporter.info("", context="CLI")
            return 0

        staged = detector.get_staged_files()
        relevant = detector.filter_relevant_files(staged)

        mapper = ComponentMapper(project_root, reporter)
        target_components = mapper.extract_component_names(relevant)

        reporter.info(
            f"{LaborantEmoji.AUTO} Auto mode: " f"{len(staged)} staged file(s)",
            context="CLI",
        )
        reporter.info("", context="CLI")
        reporter.info(f"{LaborantEmoji.CHANGED} Changed files:", context="CLI")
        for f in relevant:
            reporter.info(
                f"  {LaborantEmoji.FILE} {f.relative_to(project_root)}", context="CLI"
            )
        reporter.info("", context="CLI")

    if not target_components:
        reporter.info(f"{LaborantEmoji.INFO} No components to test.", context="CLI")
        reporter.info("", context="CLI")
        return 0

    # Show what would run
    mapper = ComponentMapper(project_root, reporter)

    reporter.info(f"{LaborantEmoji.DISCOVER} Would run:", context="CLI")
    reporter.info("", context="CLI")

    total_files = 0

    for component in sorted(target_components):
        if not mapper.has_tests(component):
            reporter.warning(
                f"  {LaborantEmoji.NO_TESTS} {component} (no tests)", context="CLI"
            )
            continue

        test_files = mapper.discover_test_files(component, categories)

        if not test_files:
            reporter.warning(
                f"  {LaborantEmoji.NO_TESTS} {component} " f"(no test files found)",
                context="CLI",
            )
            continue

        reporter.info(f"  {LaborantEmoji.COMPONENT} {component}", context="CLI")

        for category in ["unit", "integration", "e2e"]:
            if category not in test_files:
                continue

            # Get category emoji
            cat_emoji = {
                "unit": LaborantEmoji.UNIT,
                "integration": LaborantEmoji.INTEGRATION,
                "e2e": LaborantEmoji.E2E,
            }.get(category, LaborantEmoji.TEST)

            for test_file in test_files[category]:
                reporter.info(
                    f"      {cat_emoji} {category}/{test_file.name}", context="CLI"
                )
                total_files += 1

        reporter.info("", context="CLI")

    reporter.info(
        f"{LaborantEmoji.SUMMARY} Total: {total_files} test file(s) "
        f"would be executed",
        context="CLI",
    )
    reporter.info("", context="CLI")

    return 0


def lint_code(project_root: Path, components: list, reporter: SystemReporter) -> int:
    """
    Run code quality checks (black, isort, flake8).

    Args:
        project_root: Project root directory
        components: List of component names (empty = all)
        reporter: SystemReporter instance

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    from laborant.core.code_quality import CodeQualityChecker

    checker = CodeQualityChecker(project_root, reporter)

    # If no components specified, lint all
    if not components:
        success = checker.lint(None)
        return 0 if success else 1

    # Single component - use simple report
    if len(components) == 1:
        success = checker.lint(components[0])
        return 0 if success else 1

    # Multiple components - use multi-component report
    results = []
    for component in components:
        reporter.info("", context="CLI")
        result = checker.lint_component(component)
        results.append(result)

    # Print multi-component report
    checker.print_multi_component_report(results)

    # Check if all passed
    all_success = all(r["final_ok"] for r in results)
    return 0 if all_success else 1


def format_code(
    project_root: Path, component: Optional[str], reporter: SystemReporter
) -> int:
    """
    Auto-format code (black + isort).

    Args:
        project_root: Project root directory
        component: Component name (None = all)
        reporter: SystemReporter instance

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    from laborant.core.code_quality import CodeQualityChecker

    checker = CodeQualityChecker(project_root, reporter)
    success = checker.format(component)

    return 0 if success else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="laborant",
        description="Smart test orchestrator for Lumiere components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  laborant test                     # Auto mode (git diff)
  laborant test bridge guardian     # Test specific components
  laborant test --all               # Test all components
  laborant test --dry-run           # Show what would run
  laborant test bridge --unit       # Only unit tests for bridge
  laborant list                     # List available components
  laborant install-hook             # Install git pre-commit hook
  laborant lint                     # Check code quality (all)
  laborant lint pourtier            # Check code quality (component)
  laborant lint pourtier passeur    # Check multiple components
  laborant format                   # Format code (all)
  laborant format passeur           # Format code (component)
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(
        dest="command", help="Command to run", required=True
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument(
        "components",
        nargs="*",
        help="Component names to test (default: auto-detect from git)",
    )
    test_parser.add_argument(
        "--all",
        action="store_true",
        help="Run tests for ALL components (ignore git diff)",
    )
    test_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would run without executing"
    )
    test_parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    test_parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    test_parser.add_argument("--e2e", action="store_true", help="Run only e2e tests")
    test_parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )
    test_parser.add_argument(
        "--timeout", type=int, default=60, help="Test timeout in seconds (default: 60)"
    )

    # Lint command
    lint_parser = subparsers.add_parser(
        "lint", help="Check code quality (black, isort, flake8)"
    )
    lint_parser.add_argument(
        "components", nargs="*", help="Component names (default: all components)"
    )

    # Format command
    format_parser = subparsers.add_parser(
        "format", help="Auto-format code (black + isort)"
    )
    format_parser.add_argument(
        "component", nargs="?", help="Component name (default: all components)"
    )

    # List components command
    _ = subparsers.add_parser("list", help="List all available components")

    # Install hook command
    _ = subparsers.add_parser("install-hook", help="Install git pre-commit hook")

    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet mode (minimal output)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Determine project root
    project_root = Path.cwd()

    # Initialize reporter for CLI operations
    cli_reporter = SystemReporter(
        name="laborant_cli",
        log_dir="logs",
        level=10 if args.verbose else 20,
        verbose=2 if args.verbose else 1,
    )

    try:
        # Handle subcommands
        if args.command == "test":
            components = args.components if args.components else None

            if args.dry_run:
                # Build categories list
                categories = None
                if args.unit or args.integration or args.e2e:
                    categories = []
                    if args.unit:
                        categories.append("unit")
                    if args.integration:
                        categories.append("integration")
                    if args.e2e:
                        categories.append("e2e")

                return dry_run(
                    project_root, components, args.all, categories, cli_reporter
                )

            # Normal test execution mode
            # Build categories list
            categories = None
            if args.unit or args.integration or args.e2e:
                categories = []
                if args.unit:
                    categories.append("unit")
                if args.integration:
                    categories.append("integration")
                if args.e2e:
                    categories.append("e2e")

            # Create orchestrator
            laborant = Laborant(
                project_root=project_root,
                verbose=args.verbose,
                timeout=args.timeout,
                fail_fast=args.fail_fast,
            )

            # Run tests
            success = laborant.run(
                components=components, categories=categories, skip_git=args.all
            )

            # Exit with appropriate code
            return 0 if success else 1

        elif args.command == "lint":
            return lint_code(project_root, args.components, cli_reporter)

        elif args.command == "format":
            return format_code(project_root, args.component, cli_reporter)

        elif args.command == "list":
            return list_components(project_root, cli_reporter)

        elif args.command == "install-hook":
            return install_hook(project_root, cli_reporter)

    except KeyboardInterrupt:
        cli_reporter.warning(
            f"\n{LaborantEmoji.STOPPED} Test run interrupted by user", context="CLI"
        )
        return 2

    except Exception as e:
        cli_reporter.error(
            f"{LaborantEmoji.TEST_ERROR} Fatal error: {e}", context="CLI"
        )
        if args.verbose:
            import traceback

            cli_reporter.error(traceback.format_exc(), context="CLI")
        return 2


if __name__ == "__main__":
    sys.exit(main())
