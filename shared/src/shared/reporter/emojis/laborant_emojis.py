"""
Laborant test orchestration emoji definitions.

Emojis for test execution, components, and results.
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class LaborantEmoji(ComponentEmoji):
    """
    Test orchestration and component testing emojis.

    Categories:
        - Testing: Test execution and results
        - Components: Component operations
        - Files: File and directory operations
        - Results: Test outcomes
    """

    # ============================================================
    # Testing Operations
    # ============================================================
    TEST = "🧪"  # Test execution
    TEST_RUN = "🔬"  # Test runner active
    TEST_SUITE = "📋"  # Test suite
    TEST_FILE = "📄"  # Test file
    TEST_PASS = "✅"  # Test passed
    TEST_FAIL = "❌"  # Test failed
    TEST_ERROR = "💥"  # Test error
    TEST_SKIP = "⏭️"  # Test skipped

    # ============================================================
    # Test Categories
    # ============================================================
    UNIT = "📦"  # Unit tests
    INTEGRATION = "🔗"  # Integration tests
    E2E = "🌐"  # End-to-end tests

    # ============================================================
    # Components
    # ============================================================
    COMPONENT = "🧩"  # Component
    COMPONENT_PASS = "✅"  # Component all tests passed
    COMPONENT_FAIL = "❌"  # Component has failures
    NO_TESTS = "⚠️"  # Component has no tests

    # ============================================================
    # File Operations
    # ============================================================
    FILE = "📄"  # File
    FOLDER = "📁"  # Directory/folder
    CHANGED = "📝"  # Changed file
    STAGED = "➕"  # Staged file

    # ============================================================
    # Git Operations
    # ============================================================
    GIT = "🔀"  # Git operation
    GIT_DIFF = "🔍"  # Git diff
    GIT_COMMIT = "💾"  # Git commit
    GIT_BLOCK = "🚫"  # Commit blocked

    # ============================================================
    # Results & Summary
    # ============================================================
    SUMMARY = "📊"  # Summary/statistics
    SUCCESS = "🎉"  # All tests passed
    FAILURE = "💔"  # Tests failed
    WARNING = "⚠️"  # Warning message
    INFO = "ℹ️"  # Information

    # ============================================================
    # Execution States
    # ============================================================
    RUNNING = "▶️"  # Execution in progress
    STOPPED = "⏹️"  # Execution stopped
    TIMEOUT = "⏱️"  # Timeout occurred
    DURATION = "⏱️"  # Duration/timing

    # ============================================================
    # Discovery
    # ============================================================
    DISCOVER = "🔍"  # Discovery operation
    FOUND = "✓"  # Item found
    NOT_FOUND = "✗"  # Item not found
    SEARCHING = "🔎"  # Searching

    # ============================================================
    # Modes
    # ============================================================
    AUTO = "🤖"  # Auto mode
    MANUAL = "👤"  # Manual mode
    DRY_RUN = "🏃"  # Dry run mode
    VERBOSE = "📢"  # Verbose mode
