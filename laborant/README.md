# Laborant - Smart Test Orchestrator

**Intelligent test runner for the Lumiere ecosystem with git change detection and component-aware execution.**

---

## Overview

Laborant is a custom async test orchestrator that intelligently runs tests based on git changes. It detects modified files, maps them to components, executes tests in priority order (unit → integration → e2e), and provides beautiful terminal output.

**Name Origin:** *Laborant* (German/French) = "laboratory assistant" or "test technician"

**Key Feature:** Runs only tests affected by your changes, not the entire suite.

---

## Features

### Smart Test Detection
- Git diff integration for change detection
- Component mapping from file paths
- Automatic test discovery by category
- Filter irrelevant files (docs, configs)

### Test Execution
- Strict execution order: unit → integration → e2e
- Timeout handling per test file
- Fail-fast mode support
- JSON result protocol

### Code Quality
- Auto-fix with black, isort, autoflake, autopep8
- Verification with flake8
- Multi-component linting support
- Beautiful Rich terminal reports

### Visual Reporting
- Rich terminal UI with panels and colors
- Per-test result display
- Category-wise breakdown
- Component summaries
- Final verdict with commit decision

### Git Integration
- Pre-commit hook installation
- Blocks commits on test failures
- Staged file detection
- Commit bypass with `--no-verify`

---

## Quick Start

### Installation
```bash
# Install as editable package
pip install -e .
```

### Basic Usage
```bash
# Auto mode (detects changes via git diff)
laborant test

# Test specific components
laborant test pourtier passeur

# Test all components (ignore git)
laborant test --all

# Dry run (show what would run)
laborant test --dry-run

# Filter by category
laborant test --unit              # Only unit tests
laborant test --integration       # Only integration tests
laborant test --e2e              # Only e2e tests
```

---

## Commands

### Test Execution
```bash
# Auto-detect from git
laborant test

# Specific components
laborant test pourtier
laborant test pourtier passeur shared

# All components
laborant test --all

# Category filters
laborant test pourtier --unit
laborant test --integration --e2e

# Options
laborant test --dry-run          # Show without executing
laborant test --fail-fast        # Stop on first failure
laborant test --timeout 120      # Custom timeout (seconds)
laborant test -v                 # Verbose output
```

### Code Quality
```bash
# Lint (auto-fix + verify)
laborant lint                    # All components
laborant lint pourtier           # Single component
laborant lint pourtier passeur   # Multiple components

# Format (black + isort)
laborant format                  # All components
laborant format pourtier         # Single component
```

### Utilities
```bash
# List available components
laborant list

# Install git pre-commit hook
laborant install-hook
```

---

## Component Structure

Laborant expects this structure:
```
component_name/
├── tests/
│   ├── unit/              # Unit tests
│   │   └── test_*.py
│   ├── integration/       # Integration tests
│   │   └── test_*.py
│   └── e2e/              # End-to-end tests
│       └── test_*.py
└── ...
```

---

## Writing Tests

### Example Test
```python
from shared.tests import LaborantTest

class TestUserFeature(LaborantTest):
    """Test user feature."""
    
    component_name = "pourtier"
    test_category = "unit"
    
    def setup(self):
        """Setup before all tests (optional)."""
        self.test_data = {"user_id": "123"}
    
    def teardown(self):
        """Cleanup after all tests (optional)."""
        self.test_data = None
    
    def setup_test(self):
        """Setup before each test (optional)."""
        self.counter = 0
    
    def teardown_test(self):
        """Cleanup after each test (optional)."""
        pass
    
    def test_feature_works(self):
        """Test that feature works."""
        result = self.calculate_something()
        assert result == expected_value

    def calculate_something(self):
        """Helper method (not a test)."""
        return 42

if __name__ == "__main__":
    TestUserFeature.run_as_main()
```

---

## Git Integration

### Install Pre-commit Hook
```bash
laborant install-hook
```

This creates `.git/hooks/pre-commit` that:
1. Runs `laborant test` on staged files
2. Blocks commit if tests fail
3. Allows commit if tests pass

### Bypass Hook
```bash
# Skip pre-commit hook
git commit --no-verify
```

---

## Change Detection

### How It Works

1. **Git Diff:** Detect staged files via `git diff --cached`
2. **Filter:** Remove irrelevant files (docs, configs)
3. **Map:** Extract component names from file paths
4. **Discover:** Find test files for affected components
5. **Execute:** Run tests in order (unit → integration → e2e)
6. **Report:** Display results with commit decision

---

## Test Execution Order

Tests always execute in strict order:
```
Unit Tests → Integration Tests → E2E Tests
```

**Why?**
- Unit tests are fastest (catch simple bugs early)
- Integration tests verify component interactions
- E2E tests validate complete workflows

---

## Related Components

- [Pourtier](../pourtier) - Uses Laborant for testing
- [Shared](../shared) - LaborantTest base class
- All components - Tested by Laborant

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Questions?** Open an issue or contact: dev@lumiere.trade
