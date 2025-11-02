"""
Main Emoji registry class with centralized access to all emoji categories.

Provides the primary interface for accessing emojis throughout the application
with semantic organization, introspection, and helper utilities.

Usage:
    >>> from shared.reporter.emojis import Emoji
    >>>
    >>> # Category access
    >>> Emoji.SYSTEM.STARTUP        # "🚀"
    >>> Emoji.TRADING.BUY           # "🟢"
    >>> Emoji.ERROR.CRITICAL        # "🔴"
    >>>
    >>> # Shortcuts
    >>> Emoji.SUCCESS               # "✅"
    >>> Emoji.FAILURE               # "❌"
    >>>
    >>> # Formatting
    >>> Emoji.format('SYSTEM', 'STARTUP', 'Server started')
    >>> '🚀 Server started'

Version: 1.0.0
"""

from typing import Dict, List, Type

from shared.reporter.emojis.base_emojis import ComponentEmoji, EmojiCategory
from shared.reporter.emojis.database_emojis import DatabaseEmoji
from shared.reporter.emojis.errors_emojis import ErrorEmoji
from shared.reporter.emojis.event_emojis import EventEmoji
from shared.reporter.emojis.indicator_emojis import IndicatorEmoji
from shared.reporter.emojis.messaging_emojis import MessageEmoji
from shared.reporter.emojis.network_emojis import NetworkEmoji
from shared.reporter.emojis.state_emojis import StateEmoji
from shared.reporter.emojis.system_emojis import SystemEmoji
from shared.reporter.emojis.trading_emojis import TradingEmoji


class Emoji:
    """
    Central emoji registry with semantic categories.

    Provides unified access point to all emoji definitions organized
    by component and operation type. This is the main interface that
    all application code should use.

    Design Principles:
        - Single Source of Truth for all emojis
        - Semantic naming (SYSTEM.STARTUP vs magic string "🚀")
        - Namespace separation (prevents conflicts)
        - IDE autocomplete support
        - Easy introspection and discovery

    Architecture:
        Each category (SYSTEM, TRADING, etc.) is a separate class
        defined in its own module. This class aggregates them all
        for convenient access.

    Usage Patterns:
        >>> # Direct access (most common)
        >>> print(f"{Emoji.SYSTEM.STARTUP} Initializing...")
        🚀 Initializing...

        >>> # Dynamic access
        >>> emoji = Emoji.format('TRADING', 'BUY', 'Position opened')
        🟢 Position opened

        >>> # Discovery
        >>> results = Emoji.search('error')
        {'ERROR': ['ERROR', 'VALIDATION_ERROR', ...]}

        >>> # Introspection
        >>> all_emojis = Emoji.get_all_emojis()
        >>> total = Emoji.count_total()

    Categories:
        SYSTEM: System operations and lifecycle
        DATABASE: Database and persistence
        TRADING: Trading operations and signals
        INDICATOR: Technical indicators
        NETWORK: Network and communication
        MESSAGE: Messaging and notifications
        ERROR: Error levels and warnings
        STATE: State machine states
        EVENT: Event bus operations
    """

    # ============================================================
    # Emoji Categories (Aggregated from separate modules)
    # ============================================================

    SYSTEM = SystemEmoji
    DATABASE = DatabaseEmoji
    TRADING = TradingEmoji
    INDICATOR = IndicatorEmoji
    NETWORK = NetworkEmoji
    MESSAGE = MessageEmoji
    ERROR = ErrorEmoji
    STATE = StateEmoji
    EVENT = EventEmoji

    # ============================================================
    # Common Shortcuts (Most frequently used emojis)
    # ============================================================

    SUCCESS = "✅"  # Generic success
    FAILURE = "❌"  # Generic failure
    INFO = "ℹ️"  # Information
    WARNING = "⚠️"  # Warning
    QUESTION = "❓"  # Question/unknown
    CHECK = "✔️"  # Checkmark
    CROSS = "✖️"  # Cross/cancel
    LOADING = "⏳"  # Loading/in progress
    DONE = "✅"  # Task completed
    ROCKET = "🚀"  # Quick access to startup emoji

    # ============================================================
    # Category Discovery & Introspection
    # ============================================================

    @classmethod
    def get_all_categories(cls) -> Dict[str, Type[ComponentEmoji]]:
        """
        Get all registered emoji categories.

        Returns a mapping of category names to their emoji classes.
        Useful for introspection, documentation generation, and
        dynamic category access.

        Returns:
            Dictionary mapping category name to emoji class

        Example:
            >>> categories = Emoji.get_all_categories()
            >>> print(list(categories.keys()))
            ['SYSTEM', 'DATABASE', 'TRADING', 'INDICATOR', ...]

            >>> # Access category dynamically
            >>> category = categories['SYSTEM']
            >>> print(category.STARTUP)
            🚀
        """
        return {
            name: attr
            for name, attr in vars(cls).items()
            if (
                not name.startswith("_")
                and isinstance(attr, type)
                and issubclass(attr, ComponentEmoji)
            )
        }

    @classmethod
    def get_all_emojis(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all emojis from all categories.

        Returns a nested dictionary with complete emoji inventory.
        Useful for documentation, testing, and emoji picker UIs.

        Returns:
            Nested dictionary: {category: {name: emoji}}

        Example:
            >>> emojis = Emoji.get_all_emojis()
            >>> print(emojis['SYSTEM']['STARTUP'])
            🚀
            >>> print(emojis['TRADING']['BUY'])
            🟢

            >>> # Count emojis per category
            >>> for cat, emoji_dict in emojis.items():
            ...     print(f"{cat}: {len(emoji_dict)} emojis")
            SYSTEM: 15 emojis
            DATABASE: 18 emojis
            ...
        """
        result = {}

        for category_name, category_class in cls.get_all_categories().items():
            result[category_name] = category_class.get_all()

        return result

    @classmethod
    def get_category_metadata(cls) -> List[EmojiCategory]:
        """
        Get metadata for all emoji categories.

        Returns structured metadata about each category including
        name, description, and the associated emoji class. Useful
        for generating documentation and help systems.

        Returns:
            List of EmojiCategory objects with metadata

        Example:
            >>> metadata = Emoji.get_category_metadata()
            >>> for cat in metadata:
            ...     print(f"{cat.name}: {cat.description}")
            ...     print(f"  Emojis: {len(cat.get_emojis())}")
            SYSTEM: System operations and lifecycle
              Emojis: 15
            DATABASE: Database and persistence operations
              Emojis: 18
            ...
        """
        metadata = [
            EmojiCategory("SYSTEM", "System operations and lifecycle", SystemEmoji),
            EmojiCategory(
                "DATABASE", "Database and persistence operations", DatabaseEmoji
            ),
            EmojiCategory("TRADING", "Trading operations and signals", TradingEmoji),
            EmojiCategory(
                "INDICATOR", "Technical indicators and analysis", IndicatorEmoji
            ),
            EmojiCategory("NETWORK", "Network and communication", NetworkEmoji),
            EmojiCategory("MESSAGE", "Messaging and notifications", MessageEmoji),
            EmojiCategory("ERROR", "Error levels and debugging", ErrorEmoji),
            EmojiCategory("STATE", "State machine states", StateEmoji),
            EmojiCategory("EVENT", "Event bus operations", EventEmoji),
        ]

        return metadata

    # ============================================================
    # Formatting & Message Helpers
    # ============================================================

    @classmethod
    def format(cls, category: str, name: str, message: str) -> str:
        """
        Format a message with appropriate emoji from category.

        Provides dynamic emoji selection and formatting. If the
        emoji is not found, returns the message unchanged (graceful
        degradation).

        Args:
            category: Category name (e.g., 'SYSTEM', 'TRADING')
            name: Emoji name (e.g., 'STARTUP', 'BUY')
            message: Message to format

        Returns:
            Formatted message with emoji prefix, or original message
            if emoji not found

        Examples:
            >>> Emoji.format('SYSTEM', 'STARTUP', 'Server initialized')
            '🚀 Server initialized'

            >>> Emoji.format('TRADING', 'BUY', 'Opened position')
            '🟢 Opened position'

            >>> Emoji.format('ERROR', 'CRITICAL', 'Fatal error')
            '🔴 Fatal error'

            >>> # Graceful fallback
            >>> Emoji.format('INVALID', 'MISSING', 'Test')
            'Test'
        """
        try:
            category_class = getattr(cls, category.upper())
            emoji = getattr(category_class, name.upper())
            return f"{emoji} {message}"
        except AttributeError:
            # Graceful fallback: return message without emoji
            return message

    @classmethod
    def get(cls, category: str, name: str, default: str = "❓") -> str:
        """
        Get emoji by category and name with fallback default.

        Safer alternative to direct access when emoji might not exist.
        Returns default emoji if requested emoji is not found.

        Args:
            category: Category name
            name: Emoji name
            default: Default emoji to return if not found

        Returns:
            Emoji character or default

        Examples:
            >>> Emoji.get('SYSTEM', 'STARTUP')
            '🚀'

            >>> Emoji.get('TRADING', 'BUY')
            '🟢'

            >>> # Fallback to default
            >>> Emoji.get('INVALID', 'MISSING', '❓')
            '❓'

            >>> # Custom default
            >>> Emoji.get('INVALID', 'MISSING', '⚠️')
            '⚠️'
        """
        try:
            category_class = getattr(cls, category.upper())
            return getattr(category_class, name.upper())
        except AttributeError:
            return default

    # ============================================================
    # Search & Discovery
    # ============================================================

    @classmethod
    def search(cls, keyword: str) -> Dict[str, List[str]]:
        """
        Search for emojis by keyword in names (case-insensitive).

        Useful for discovering available emojis and their categories.
        Helps developers find the right emoji without browsing code.

        Args:
            keyword: Search term (case-insensitive)

        Returns:
            Dictionary mapping category to list of matching emoji names

        Examples:
            >>> # Find startup-related emojis
            >>> results = Emoji.search('start')
            >>> print(results)
            {'SYSTEM': ['STARTUP'], 'TRADING': ['STRATEGY_START']}

            >>> # Find all error-related emojis
            >>> results = Emoji.search('error')
            >>> print(results)
            {'ERROR': ['ERROR', 'VALIDATION_ERROR', 'HANDLER_ERROR']}

            >>> # Find connection-related emojis
            >>> results = Emoji.search('connect')
            >>> print(results)
            {'NETWORK': ['CONNECTED', 'DISCONNECTED', 'RECONNECTING']}
        """
        keyword = keyword.upper()
        results = {}

        for category_name, category_class in cls.get_all_categories().items():
            matches = [name for name in category_class.list_names() if keyword in name]

            if matches:
                results[category_name] = matches

        return results

    @classmethod
    def list_category_emojis(cls, category: str) -> List[str]:
        """
        List all emoji names in a specific category.

        Args:
            category: Category name (e.g., 'SYSTEM', 'TRADING')

        Returns:
            List of emoji names in that category

        Example:
            >>> emojis = Emoji.list_category_emojis('SYSTEM')
            >>> print(emojis[:5])
            ['STARTUP', 'SHUTDOWN', 'READY', 'RESTART', 'INIT']
        """
        try:
            category_class = getattr(cls, category.upper())
            return category_class.list_names()
        except AttributeError:
            return []

    # ============================================================
    # Statistics & Counting
    # ============================================================

    @classmethod
    def count_total(cls) -> int:
        """
        Count total number of emojis across all categories.

        Returns:
            Total emoji count

        Example:
            >>> total = Emoji.count_total()
            >>> print(f"Total emojis available: {total}")
            Total emojis available: 150
        """
        total = 0
        for category_class in cls.get_all_categories().values():
            total += len(category_class.get_all())
        return total

    @classmethod
    def count_by_category(cls) -> Dict[str, int]:
        """
        Count emojis per category.

        Returns:
            Dictionary mapping category name to emoji count

        Example:
            >>> counts = Emoji.count_by_category()
            >>> for cat, count in counts.items():
            ...     print(f"{cat}: {count}")
            SYSTEM: 15
            DATABASE: 18
            TRADING: 25
            ...
        """
        return {
            category_name: len(category_class.get_all())
            for category_name, category_class in cls.get_all_categories().items()
        }

    # ============================================================
    # Validation
    # ============================================================

    @classmethod
    def exists(cls, category: str, name: str) -> bool:
        """
        Check if an emoji exists in a category.

        Args:
            category: Category name
            name: Emoji name

        Returns:
            True if emoji exists, False otherwise

        Example:
            >>> Emoji.exists('SYSTEM', 'STARTUP')
            True
            >>> Emoji.exists('SYSTEM', 'NONEXISTENT')
            False
        """
        try:
            category_class = getattr(cls, category.upper())
            getattr(category_class, name.upper())
            return True
        except AttributeError:
            return False

    @classmethod
    def validate_usage(cls, category: str, name: str) -> tuple[bool, str]:
        """
        Validate emoji usage and provide helpful message.

        Args:
            category: Category name
            name: Emoji name

        Returns:
            Tuple of (is_valid, message)

        Example:
            >>> valid, msg = Emoji.validate_usage('SYSTEM', 'STARTUP')
            >>> print(valid, msg)
            True "Valid: Emoji.SYSTEM.STARTUP = 🚀"

            >>> valid, msg = Emoji.validate_usage('INVALID', 'MISSING')
            >>> print(valid, msg)
            False "Category 'INVALID' not found. Available: SYSTEM, DATABASE, ..."
        """
        try:
            category_class = getattr(cls, category.upper())
        except AttributeError:
            categories = ", ".join(cls.get_all_categories().keys())
            return False, (
                f"Category '{category}' not found. " f"Available: {categories}"
            )

        try:
            emoji = getattr(category_class, name.upper())
            return True, (f"Valid: Emoji.{category.upper()}.{name.upper()} = {emoji}")
        except AttributeError:
            available = ", ".join(category_class.list_names()[:5])
            return False, (
                f"Emoji '{name}' not found in {category}. "
                f"Available: {available}, ..."
            )


# ============================================================
# Convenience Functions (Module-level helpers)
# ============================================================


def get_emoji(category: str, name: str, default: str = "❓") -> str:
    """
    Convenience function to get emoji with fallback.

    Alias for Emoji.get() for backwards compatibility and
    functional programming style.

    Args:
        category: Category name
        name: Emoji name
        default: Default emoji if not found

    Returns:
        Emoji character or default

    Example:
        >>> get_emoji('SYSTEM', 'STARTUP')
        '🚀'
    """
    return Emoji.get(category, name, default)


def format_with_emoji(
    category: str, name: str, message: str, fallback: bool = True
) -> str:
    """
    Format message with emoji, optionally falling back to plain text.

    Args:
        category: Emoji category
        name: Emoji name
        message: Message to format
        fallback: If True, return message without emoji if not found;
                 if False, include [CATEGORY.NAME] prefix

    Returns:
        Formatted message

    Examples:
        >>> format_with_emoji('SYSTEM', 'STARTUP', 'Server started')
        '🚀 Server started'

        >>> # With fallback=True (default)
        >>> format_with_emoji('INVALID', 'MISSING', 'Test')
        'Test'

        >>> # With fallback=False
        >>> format_with_emoji('INVALID', 'MISSING', 'Test', fallback=False)
        '[INVALID.MISSING] Test'
    """
    emoji = get_emoji(category, name, "")

    if emoji:
        return f"{emoji} {message}"
    elif fallback:
        return message
    else:
        return f"[{category}.{name}] {message}"
