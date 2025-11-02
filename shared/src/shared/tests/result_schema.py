"""
Test result schema validation and parsing.

Defines the JSON contract between test files and laborant.
Single source of truth for result format.
"""

import json
from typing import Any, Dict, Optional, Tuple

from shared.tests.models import TestStatus

# Schema version - increment on breaking changes
SCHEMA_VERSION = "1.0"

# Required top-level fields in test output
REQUIRED_FIELDS = [
    "schema_version",
    "test_file",
    "component",
    "category",
    "total",
    "passed",
    "failed",
    "errors",
    "skipped",
    "duration",
    "timestamp",
    "tests",
    "metadata",
]

# Valid test categories
VALID_CATEGORIES = ["unit", "integration", "e2e"]

# Valid test statuses
VALID_STATUSES = [s.value for s in TestStatus]

# Output markers for parsing
START_MARKER = "===LABORANT_RESULTS==="
END_MARKER = "===LABORANT_RESULTS_END==="


def validate_test_output(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate test output against schema.

    Args:
        data: Parsed JSON data from test output

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    # Check all required fields exist
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate schema version
    if data["schema_version"] != SCHEMA_VERSION:
        return (
            False,
            f"Schema version mismatch: "
            f"{data['schema_version']} != {SCHEMA_VERSION}",
        )

    # Validate category
    if data["category"] not in VALID_CATEGORIES:
        return False, f"Invalid category: {data['category']}"

    # Validate counts match
    if data["total"] != len(data["tests"]):
        return (
            False,
            f"Total count mismatch: " f"{data['total']} != {len(data['tests'])}",
        )

    # Validate individual test results
    for test in data["tests"]:
        if "status" not in test:
            return False, "Test result missing status field"
        if test["status"] not in VALID_STATUSES:
            return False, f"Invalid test status: {test['status']}"

    # Validate aggregates match actual counts
    passed = sum(1 for t in data["tests"] if t["status"] == "pass")
    failed = sum(1 for t in data["tests"] if t["status"] == "fail")
    errors = sum(1 for t in data["tests"] if t["status"] == "error")

    if data["passed"] != passed:
        return False, "Passed count mismatch"
    if data["failed"] != failed:
        return False, "Failed count mismatch"
    if data["errors"] != errors:
        return False, "Errors count mismatch"

    return True, None


def parse_test_output(stdout: str) -> Optional[Dict[str, Any]]:
    """
    Parse test output and extract JSON results.

    Looks for content between START_MARKER and END_MARKER.

    Args:
        stdout: Complete stdout from test execution

    Returns:
        Parsed JSON dict or None if parsing failed
    """
    try:
        start_idx = stdout.find(START_MARKER)
        end_idx = stdout.find(END_MARKER)

        if start_idx == -1 or end_idx == -1:
            return None

        # Extract JSON between markers
        json_start = start_idx + len(START_MARKER)
        json_str = stdout[json_start:end_idx].strip()

        return json.loads(json_str)

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def format_output(data: Dict[str, Any]) -> str:
    """
    Format test results as standard output.

    Wraps JSON in markers for parsing by laborant.

    Args:
        data: Test results dictionary

    Returns:
        Formatted output string with markers
    """
    json_str = json.dumps(data, indent=2)
    return f"{START_MARKER}\n{json_str}\n{END_MARKER}"
