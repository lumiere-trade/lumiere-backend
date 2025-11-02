"""
Base classes for emoji registry components.

Provides foundation for all emoji category classes with
consistent structure and introspection support.

Version: 1.0.0
"""

from typing import Dict, List, Type


class ComponentEmoji:
    """
    Base class for component-specific emoji collections.

    All emoji category classes inherit from this to maintain
    consistent structure and enable introspection capabilities.

    Design:
        - Each subclass represents a semantic category
        - Class attributes define emojis as constants
        - No instance methods needed (all class-level)

    Example:
        >>> class MyEmoji(ComponentEmoji):
        ...     HELLO = "👋"
        ...     WORLD = "🌍"
    """

    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """
        Get all emoji definitions from this category.

        Returns:
            Dictionary mapping emoji name to emoji character

        Example:
            >>> SystemEmoji.get_all()
            {'STARTUP': '🚀', 'SHUTDOWN': '🛑', ...}
        """
        return {
            name: value
            for name, value in vars(cls).items()
            if not name.startswith("_") and isinstance(value, str)
        }

    @classmethod
    def list_names(cls) -> List[str]:
        """
        Get list of all emoji names in this category.

        Returns:
            List of emoji constant names

        Example:
            >>> SystemEmoji.list_names()
            ['STARTUP', 'SHUTDOWN', 'READY', ...]
        """
        return [
            name for name in dir(cls) if not name.startswith("_") and name.isupper()
        ]


class EmojiCategory:
    """
    Container for emoji category metadata.

    Used for documentation and introspection of emoji categories.
    """

    def __init__(self, name: str, description: str, emoji_class: Type[ComponentEmoji]):
        """
        Initialize emoji category metadata.

        Args:
            name: Category name (e.g., "System", "Trading")
            description: Brief description of category purpose
            emoji_class: The ComponentEmoji subclass for this category
        """
        self.name = name
        self.description = description
        self.emoji_class = emoji_class

    def get_emojis(self) -> Dict[str, str]:
        """Get all emojis in this category."""
        return self.emoji_class.get_all()
