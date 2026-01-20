# Laborant - Smart Test Orchestrator

**Version:** 0.1.0
**Last Updated:** January 20, 2026
**Component Type:** Intelligent Test Runner with Git Integration and Code Quality Enforcement

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Test Execution Flow](#4-test-execution-flow)
5. [Code Quality System](#5-code-quality-system)
6. [Git Integration](#6-git-integration)
7. [CLI Reference](#7-cli-reference)
8. [Test Protocol](#8-test-protocol)
9. [Visual Reporting](#9-visual-reporting)
10. [Integration Points](#10-integration-points)
11. [Troubleshooting Guide](#11-troubleshooting-guide)

---

## 1. Executive Summary

### 1.1 Purpose

Laborant is Lumière's **intelligent test orchestrator** that detects code changes via git, maps them to affected components, and executes tests in strict priority order (unit → integration → e2e). It enforces code quality standards through automated linting and provides beautiful terminal output via Rich.

**Name Origin:** *Laborant* (German/French) = "laboratory assistant" or "test technician"

### 1.2 Key Capabilities

- **Smart Change Detection**: Git diff integration for automatic component detection
- **Component Mapping**: Maps changed files to components and discovers their tests
- **Strict Execution Order**: Always runs unit → integration → e2e tests
- **Code Quality Enforcement**: Auto-fix with black, isort, autoflake, autopep8; verify with flake8
- **Git Pre-commit Hook**: Automatically blocks commits with failing tests or lint issues
- **Beautiful Terminal UI**: Rich-based panels, colors, and progress indicators
- **JSON Test Protocol**: Standardized test result format via shared package
- **Fail-Fast Mode**: Stop on first failure for quick feedback
- **Dry Run**: Preview what would be executed without running tests

### 1.3 Design Philosophy

**Key Principles:**
- **Only Test What Changed**: Don't run entire test suite on every commit
- **Strict Execution Order**: Unit tests catch simple bugs before expensive integration tests
- **Auto-fix Code Quality**: Don't ask developers to fix formatting manually
- **Visual Excellence**: Terminal output should be informative and beautiful
- **Git Native**: Integrate seamlessly with git workflow
- **Zero Configuration**: Works out-of-box for standard component structure

### 1.4 Technology Stack

- **Language**: Python 3.11+
- **CLI Framework**: argparse with custom subcommands
- **Terminal UI**: Rich 13.7+ for panels, tables, and colors
- **Code Quality**: black, isort, autoflake, autopep8, flake8
- **Test Protocol**: JSON schema via shared==0.6.0
- **Git Integration**: subprocess-based git commands
- **Async Support**: asyncio for concurrent operations (future)

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                  Git Repository (User's Workspace)              │
│                                                                 │
│  .git/hooks/pre-commit  ──► Triggers Laborant on commit       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ git diff --cached
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Laborant CLI (Entry Point)                  │
│                      laborant/cli.py                            │
│                                                                 │
│  Commands:                                                      │
│  - test              Run tests (auto or manual mode)           │
│  - lint              Code quality checks + auto-fix            │
│  - format            Format code (black + isort)               │
│  - list              Show available components                 │
│  - install-hook      Install git pre-commit hook               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Delegates to Orchestrator
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  Orchestrator (Laborant Class)                  │
│                   laborant/core/orchestrator.py                 │
│                                                                 │
│  Responsibilities:                                              │
│  - Coordinate all components                                   │
│  - Manage test execution lifecycle                             │
│  - Aggregate results                                            │
│  - Control fail-fast behavior                                  │
│  - Print final summary                                          │
└──────┬──────────────┬──────────────┬──────────────┬────────────┘
       │              │              │              │
       │              │              │              │
   ┌───▼───┐    ┌─────▼────┐   ┌────▼─────┐   ┌────▼────┐
   │Change │    │Component │   │   Test   │   │Reporter │
   │Detect │    │  Mapper  │   │ Executor │   │ (Rich)  │
   └───┬───┘    └─────┬────┘   └────┬─────┘   └────┬────┘
       │              │              │              │
       │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼─────────────┐
│                    Core Components                              │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ChangeDetector (change_detector.py)                   │   │
│  │  - Git diff integration                                │   │
│  │  - Staged file detection                               │   │
│  │  - Relevant file filtering                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ComponentMapper (component_mapper.py)                 │   │
│  │  - File path → component name mapping                  │   │
│  │  - Test discovery by category                          │   │
│  │  - Component structure validation                      │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  TestExecutor (test_executor.py)                       │   │
│  │  - Subprocess-based test execution                     │   │
│  │  - JSON protocol parsing                               │   │
│  │  - Timeout handling                                     │   │
│  │  - Error result creation                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  LaborantReporter (reporter.py)                        │   │
│  │  - Rich Panel creation                                 │   │
│  │  - Component headers                                   │   │
│  │  - Test result panels                                  │   │
│  │  - Category summaries                                  │   │
│  │  - Final summary                                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  CodeQualityChecker (code_quality.py)                  │   │
│  │  - black formatter                                     │   │
│  │  - isort import sorter                                 │   │
│  │  - autoflake unused code remover                       │   │
│  │  - autopep8 PEP8 fixer                                 │   │
│  │  - flake8 linter                                       │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Reads test files
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Component Test Structure                           │
│                                                                 │
│  component_name/                                                │
│  ├── tests/                                                     │
│  │   ├── unit/              Unit tests (fast, isolated)        │
│  │   │   └── test_*.py                                         │
│  │   ├── integration/       Integration tests (services)       │
│  │   │   └── test_*.py                                         │
│  │   └── e2e/              End-to-end tests (full flows)       │
│  │       └── test_*.py                                         │
│  └── src/                                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interactions

**Auto Mode (Git Detection) Flow:**
```
User commits code
    ↓
Git pre-commit hook triggers
    ↓
laborant test (no args)
    ↓
ChangeDetector.get_staged_files()
    ↓
Filter irrelevant files (.md, .txt, etc.)
    ↓
ComponentMapper.extract_component_names()
    ↓
ComponentMapper.discover_test_files()
    ↓
Orchestrator.run()
    ↓
For each component in sorted order:
    ↓
    For category in [unit, integration, e2e]:
        ↓
        For test_file in category:
            ↓
            TestExecutor.execute_test_file()
                ↓
                subprocess.run([python, test_file])
                ↓
                Parse JSON output
                ↓
                Return TestFileResult
            ↓
            LaborantReporter.create_test_file_panel()
            ↓
            Print panel to console
    ↓
    LaborantReporter.create_component_summary()
    ↓
LaborantReporter.create_final_summary()
    ↓
Exit code 0 (allow commit) or 1 (block commit)
```

**Manual Mode Flow:**
```
User: laborant test pourtier passeur
    ↓
CLI parses arguments
    ↓
Orchestrator.run(components=['pourtier', 'passeur'])
    ↓
Skip git detection (manual components specified)
    ↓
For each component in [pourtier, passeur]:
    ↓
    ComponentMapper.discover_test_files(component)
    ↓
    Execute tests in order (unit → integration → e2e)
    ↓
    Print results
    ↓
Final summary and exit code
```

**Code Quality Flow:**
```
User: laborant lint pourtier
    ↓
CodeQualityChecker.lint('pourtier')
    ↓
Step 1: run_flake8() → Detect 47 issues
    ↓
Step 2: run_autoflake() → Remove unused imports
    ↓
Step 3: run_autopep8() → Fix PEP8 violations
    ↓
Step 4: run_black() → Format code
    ↓
Step 5: run_isort() → Sort imports
    ↓
Step 6: run_flake8() → Verify (3 issues remain)
    ↓
Print report:
    - Initial: 47 issues
    - Fixed: 44 issues
    - Remaining: 3 issues (require manual fixes)
    ↓
Exit code 0 if no issues, 1 if manual fixes needed
```

---

## 3. Core Components

### 3.1 Change Detector

**File**: `laborant/core/change_detector.py`

**Purpose**: Detect changed files via git and filter relevant changes.

**Key Methods:**
```python
def get_staged_files(self) -> List[Path]:
    """Get list of staged files from git diff --cached."""
    
def get_modified_files(self) -> List[Path]:
    """Get list of modified files (staged + unstaged)."""
    
def is_git_repository(self) -> bool:
    """Check if project root is a git repository."""
    
def filter_relevant_files(self, files: List[Path]) -> List[Path]:
    """Filter out irrelevant files (docs, configs, etc.)."""
```

**Filtering Logic:**
```python
# Skip root-level non-code files
SKIP_EXTENSIONS = [".md", ".txt", ".rst", ".pdf"]
SKIP_FILES = [".gitignore", ".gitattributes", "readme.md", "license"]

# Skip IDE directories
SKIP_DIRS = [".vscode", ".idea", ".git", "__pycache__"]
```

**Example Usage:**
```python
detector = ChangeDetector(project_root, reporter)

# Get staged files
staged = detector.get_staged_files()
# Returns: [Path('pourtier/src/main.py'), Path('passeur/tests/unit/test_solana.py')]

# Filter relevant
relevant = detector.filter_relevant_files(staged)
# Removes: README.md, .gitignore, etc.
# Returns: [Path('pourtier/src/main.py'), Path('passeur/tests/unit/test_solana.py')]
```

### 3.2 Component Mapper

**File**: `laborant/core/component_mapper.py`

**Purpose**: Map file paths to components and discover their tests.

**Component Convention:**
- Component = first-level directory with `tests/` subdirectory
- Test structure: `component/tests/{unit,integration,e2e}/test_*.py`

**Key Methods:**
```python
def extract_component_names(self, files: List[Path]) -> Set[str]:
    """Extract unique component names from file paths."""
    
def has_tests(self, component_name: str) -> bool:
    """Check if component has tests directory."""
    
def discover_test_files(
    self, 
    component_name: str,
    categories: Optional[List[str]] = None,
    file_pattern: Optional[str] = None
) -> Dict[str, List[Path]]:
    """Discover test files for a component."""
    
def discover_all_components(self) -> List[str]:
    """Discover all components in project."""
    
def validate_component_structure(self, component_name: str) -> Dict[str, bool]:
    """Validate component test structure."""
    
def get_component_summary(self, component_name: str) -> Dict[str, any]:
    """Get summary information about a component."""
```

**Discovery Example:**
```python
mapper = ComponentMapper(project_root, reporter)

# Extract component names from changed files
files = [
    Path('pourtier/src/routes/auth.py'),
    Path('passeur/tests/unit/test_solana.py'),
    Path('shared/reporter/system_reporter.py')
]
components = mapper.extract_component_names(files)
# Returns: {'pourtier', 'passeur', 'shared'}

# Discover tests for component
tests = mapper.discover_test_files('pourtier')
# Returns: {
#     'unit': [Path('pourtier/tests/unit/test_auth.py'), ...],
#     'integration': [Path('pourtier/tests/integration/test_api.py'), ...],
#     'e2e': []
# }

# Discover with category filter
unit_only = mapper.discover_test_files('pourtier', categories=['unit'])
# Returns: {'unit': [Path('pourtier/tests/unit/test_auth.py'), ...]}

# Discover with file pattern
specific = mapper.discover_test_files('passeur', file_pattern='test_escrow*.py')
# Returns: {'unit': [Path('passeur/tests/unit/test_escrow_creation.py'), ...]}
```

### 3.3 Test Executor

**File**: `laborant/core/test_executor.py`

**Purpose**: Execute test files as subprocess and parse JSON results.

**Execution Strategy:**
- Run tests as subprocess for isolation
- Parse JSON output using standard protocol
- Handle timeouts gracefully
- Create error results on failure

**Key Methods:**
```python
def execute_test_file(
    self, 
    test_file: Path, 
    component: str, 
    category: str
) -> TestFileResult:
    """Execute a single test file and parse results."""
    
def can_execute(self, test_file: Path) -> bool:
    """Check if test file can be executed."""
    
def _create_error_result(
    self,
    test_file: Path,
    component: str,
    category: str,
    error: str,
    stderr: str,
    duration: float
) -> TestFileResult:
    """Create error result when test execution fails."""
```

**Subprocess Execution:**
```python
# Prepare environment
test_env = os.environ.copy()
test_env["ENV"] = "test"  # Signal test mode

# Run test as subprocess
result = subprocess.run(
    [sys.executable, str(test_file)],
    cwd=str(project_root),
    capture_output=True,
    text=True,
    timeout=timeout,
    env=test_env
)

# Parse JSON output
test_data = parse_test_output(result.stdout)

# Validate schema
is_valid, error_msg = validate_test_output(test_data)

# Convert to TestFileResult
test_result = TestFileResult(**test_data)
```

### 3.4 Laborant Reporter

**File**: `laborant/core/reporter.py`

**Purpose**: Create Rich renderable objects for visual test results.

**Design Principle**: Reporter creates Rich objects but does NOT print them. Orchestrator handles rendering via Rich Console.

**Key Methods:**
```python
def create_component_header(
    self, 
    component_name: str, 
    test_discovery: Dict[str, int]
) -> Panel:
    """Create Rich Panel for component header with test discovery."""
    
def create_category_header_panel(
    self,
    category: str,
    file_count: int,
    component: str
) -> Panel:
    """Create Rich Panel for category header."""
    
def create_test_file_panel(
    self,
    test_file_path: str,
    component: str,
    category: str,
    tests: List,
    passed: int,
    total: int,
    duration: float
) -> Panel:
    """Create Rich Panel for test file with all results."""
    
def create_component_summary(
    self,
    component_name: str,
    category_results: Dict[str, List],
    total_tests: int,
    total_passed: int,
    total_failed: int,
    total_errors: int
) -> Panel:
    """Create Rich Panel for component summary with category breakdown."""
    
def create_final_summary(
    self,
    total_components: int,
    total_tests: int,
    total_passed: int,
    total_failed: int,
    total_errors: int,
    total_duration: float,
    category_breakdown: Dict[str, Dict[str, int]],
    components_with_failures: List[str],
    components_without_tests: List[str]
) -> Panel:
    """Create Rich Panel for final summary."""
```

**Visual Standards:**
- **Width**: Always 67 characters
- **Border**: White for informational panels
- **Category Colors**: Blue (unit), Magenta (integration), Green (e2e)
- **Status Colors**: Green (pass), Red (fail/error), Yellow (warning)

### 3.5 Code Quality Checker

**File**: `laborant/core/code_quality.py`

**Purpose**: Enforce code quality standards through automated tools.

**Tool Chain:**
1. **autoflake**: Remove unused imports and variables
2. **autopep8**: Fix PEP8 violations
3. **black**: Format code style (line length 88)
4. **isort**: Sort imports (black profile)
5. **flake8**: Verify code quality (final check)

**Key Methods:**
```python
def lint(self, component: Optional[str] = None) -> bool:
    """Smart linting with auto-fix and verification."""
    
def lint_component(self, component: str) -> dict:
    """Lint a component and return results dict."""
    
def format(self, component: Optional[str] = None) -> bool:
    """Auto-format code with black + isort."""
    
def run_black(self, component: Optional[str] = None) -> Tuple[bool, str]:
    """Run black formatter."""
    
def run_isort(self, component: Optional[str] = None) -> Tuple[bool, str]:
    """Run isort import sorter."""
    
def run_autoflake(self, component: Optional[str] = None) -> Tuple[bool, str]:
    """Run autoflake to remove unused code."""
    
def run_autopep8(self, component: Optional[str] = None) -> Tuple[bool, str]:
    """Run autopep8 to fix PEP8 issues."""
    
def run_flake8(self, component: Optional[str] = None) -> Tuple[bool, str]:
    """Run flake8 linter check (read-only)."""
```

---

## 4. Test Execution Flow

### 4.1 Auto Mode (Git Detection)

**Trigger**: `laborant test` (no arguments)

**Complete Flow:**
```
1. Initialize Orchestrator
   ↓
2. ChangeDetector.get_staged_files()
   - Run: git diff --cached --name-only
   - Returns: [Path('pourtier/src/auth.py'), Path('passeur/tests/unit/test_solana.py')]
   ↓
3. ChangeDetector.filter_relevant_files()
   - Remove: .md, .txt, .gitignore, etc.
   - Returns: [Path('pourtier/src/auth.py'), Path('passeur/tests/unit/test_solana.py')]
   ↓
4. ComponentMapper.extract_component_names()
   - Extract first directory level
   - Returns: {'pourtier', 'passeur'}
   ↓
5. For each component in sorted(['pourtier', 'passeur']):
   ↓
   5.1 ComponentMapper.discover_test_files(component)
   5.2 Print component header
   5.3 Execute tests (unit → integration → e2e)
   5.4 Print component summary
   ↓
6. Print final summary
   ↓
7. Exit with code 0 (pass) or 1 (fail)
```

### 4.2 Manual Mode (Specific Components)

**Trigger**: `laborant test pourtier passeur`

**Flow:**
```
1. CLI parses arguments: components = ['pourtier', 'passeur']
2. Skip git detection (manual mode)
3. Execute tests for specified components
4. Print final summary and exit
```

### 4.3 Category Filter Mode

**Trigger**: `laborant test --unit --integration`

**Flow:**
```
1. Build categories list: ['unit', 'integration']
2. Skip 'e2e' category during test discovery
3. Execute only unit and integration tests
```

---

## 5. Code Quality System

### 5.1 Tool Chain Architecture

**Order of Execution:**
```
flake8 (detect) → autoflake → autopep8 → black → isort → flake8 (verify)
```

**Why This Order:**
1. **flake8 first**: Establish baseline issue count
2. **autoflake**: Remove unused code (changes AST)
3. **autopep8**: Fix PEP8 violations (spacing, indentation)
4. **black**: Enforce consistent style (line breaks, quotes)
5. **isort**: Sort imports (must run after black)
6. **flake8 last**: Verify remaining issues

### 5.2 Lint Workflow

**Command**: `laborant lint pourtier`

**Process:**
```
Step 1/6: Detecting issues...
 Run: flake8 pourtier/
 Found 47 issues

Step 2/6: Removing unused code...
 Run: autoflake pourtier/
 autoflake: Done

Step 3/6: Fixing PEP8 issues...
 Run: autopep8 pourtier/
 autopep8: Done

Step 4/6: Running black...
 Run: black pourtier/
 black: Done

Step 5/6: Running isort...
 Run: isort pourtier/
 isort: Done

Step 6/6: Final verification...
 Run: flake8 pourtier/
 Fixed 44 issues automatically
 3 issues require manual fixes
```

---

## 6. Git Integration

### 6.1 Pre-commit Hook

**Installation**: `laborant install-hook`

**Location**: `.git/hooks/pre-commit`

**Template**: `laborant/hooks/pre-commit.template`

**Hook Workflow:**
```bash
#!/usr/bin/env bash
set -e

TESTS_PASSED=true
LINT_PASSED=true

# Step 1: Run tests
if python3 -m laborant test; then
    echo "[OK] Tests passed"
else
    echo "[FAIL] Tests failed"
    TESTS_PASSED=false
fi

# Step 2: Run lint on changed components
CHANGED_FILES=$(git diff --cached --name-only | grep -E '\.py$' || true)
if [ -n "$CHANGED_FILES" ]; then
    COMPONENTS=$(echo "$CHANGED_FILES" | cut -d'/' -f1 | sort -u | tr '\n' ' ')
    if python3 -m laborant lint $COMPONENTS; then
        echo "[OK] Lint passed"
    else
        echo "[FAIL] Lint failed"
        LINT_PASSED=false
    fi
fi

# Final decision
if [ "$TESTS_PASSED" = true ] && [ "$LINT_PASSED" = true ]; then
    echo "[OK] All checks passed - Commit allowed"
    exit 0
else
    echo "[FAIL] Commit blocked"
    exit 1
fi
```

### 6.2 Hook Bypass

**Skip hook temporarily:**
```bash
git commit --no-verify
```

---

## 7. CLI Reference

### 7.1 Test Command

**Syntax:**
```bash
laborant test [components...] [options]
```

**Examples:**
```bash
# Auto mode (git detection)
laborant test

# Manual mode (specific components)
laborant test pourtier passeur

# All components
laborant test --all

# Category filters
laborant test --unit
laborant test --integration
laborant test --e2e

# File pattern
laborant test passeur --file test_escrow*.py

# Options
laborant test --fail-fast
laborant test --timeout 600
laborant test --dry-run
laborant test -v
```

### 7.2 Lint Command

**Syntax:**
```bash
laborant lint [components...]
```

**Examples:**
```bash
# Lint all components
laborant lint

# Lint specific component
laborant lint pourtier

# Lint multiple components
laborant lint pourtier passeur shared
```

### 7.3 Format Command

**Syntax:**
```bash
laborant format [component]
```

**Examples:**
```bash
# Format all components
laborant format

# Format specific component
laborant format pourtier
```

### 7.4 List Command

**Syntax:**
```bash
laborant list
```

**Output:**
```
Available components:

  courier              (has tests: unit, integration)
    20 test files
  passeur              (has tests: unit, integration, e2e)
    35 test files
  pourtier             (has tests: unit, integration)
    20 test files

Total: 3 components
```

### 7.5 Install Hook Command

**Syntax:**
```bash
laborant install-hook
```

---

## 8. Test Protocol

### 8.1 JSON Schema

**Version**: 1.0.0

**TestFileResult Schema:**
```json
{
  "schema_version": "1.0.0",
  "test_file": "test_auth.py",
  "component": "pourtier",
  "category": "unit",
  "total": 15,
  "passed": 15,
  "failed": 0,
  "errors": 0,
  "skipped": 0,
  "duration": 0.234,
  "timestamp": "2026-01-20T15:30:45.123Z",
  "tests": [
    {
      "name": "test_user_registration",
      "status": "pass",
      "duration": 0.023,
      "error": null
    }
  ],
  "metadata": {}
}
```

### 8.2 Test Implementation

**Base Class**: `shared.tests.LaborantTest`

**Example:**
```python
from shared.tests import LaborantTest

class TestAuth(LaborantTest):
    component_name = "pourtier"
    test_category = "unit"
    
    def test_user_registration(self):
        result = register_user("test@example.com", "password")
        assert result.success is True

if __name__ == "__main__":
    TestAuth.run_as_main()
```

---

## 9. Visual Reporting

### 9.1 Terminal Output Standards

**Width**: 67 characters

**Color Scheme:**
- **Green**: Success
- **Red**: Failure
- **Yellow**: Warning
- **Blue**: Unit tests
- **Magenta**: Integration tests
- **White**: Borders

**Example Component Header:**
```
┌─ Pourtier ────────────────────────────────────────────────────┐
│                                                                │
│  Test Discovery:                                               │
│                                                                │
│  Unit:         9 test files                                    │
│  Integration:  11 test files                                   │
│                                                                │
│  Total: 20 test files will be executed                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 10. Integration Points

### 10.1 Shared Package

**Dependency**: `shared==0.6.0`

**Used Components:**
```python
from shared.reporter.system_reporter import SystemReporter
from shared.tests import LaborantTest
from shared.tests.models import TestFileResult, IndividualTestResult
from shared.tests.result_schema import (
    parse_test_output,
    validate_test_output,
    SCHEMA_VERSION
)
```

### 10.2 Git Integration

**Commands Used:**
```bash
# Check if git repository
git rev-parse --git-dir

# Get staged files
git diff --cached --name-only

# Get modified files
git diff --name-only HEAD

# Get changed Python files
git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$'
```

### 10.3 Component Test Files

**Expected Structure:**
```
component_name/
├── tests/
│   ├── unit/
│   │   └── test_*.py
│   ├── integration/
│   │   └── test_*.py
│   └── e2e/
│       └── test_*.py
└── src/
```

---

## 11. Troubleshooting Guide

### 11.1 Common Issues

#### Issue: "Not a git repository"

**Solution:**
```bash
# Initialize git repository
git init

# Or run with --all flag
laborant test --all
```

#### Issue: "No components with tests found"

**Solution:**
```bash
# Create test directory
mkdir -p component_name/tests/unit

# Add test file
cat > component_name/tests/unit/test_example.py << 'TESTEOF'
from shared.tests import LaborantTest

class TestExample(LaborantTest):
    component_name = "component_name"
    test_category = "unit"
    
    def test_example(self):
        assert True

if __name__ == "__main__":
    TestExample.run_as_main()
TESTEOF
```

#### Issue: "Test timeout"

**Solution:**
```bash
# Increase timeout
laborant test --timeout 600
```

#### Issue: "black not found"

**Solution:**
```bash
# Install dependencies
pip install -e .
```

### 11.2 Debug Mode

**Enable verbose output:**
```bash
laborant test -v
```

### 11.3 Git Hook Issues

**Check hook exists:**
```bash
ls -la .git/hooks/pre-commit
```

**Make executable:**
```bash
chmod +x .git/hooks/pre-commit
```

**Bypass hook:**
```bash
git commit --no-verify
```

---

## Appendix A: Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success - all tests passed |
| 1    | Failure - tests failed |
| 2    | Error - fatal error or interrupt |

---

## Appendix B: File Exclusions

**Excluded Directories:**
- `__pycache__`
- `node_modules`
- `venv`, `venv311`
- `.git`
- `.pytest_cache`
- `build`, `dist`
- `logs`
- `docs`

**Excluded Extensions:**
- `.md`
- `.txt`
- `.rst`
- `.pdf`
- `.log`

---

**END OF DOCUMENT**
