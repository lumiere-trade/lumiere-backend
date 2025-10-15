"""
Validation utility functions for Passeur.

Provides validation for Solana addresses, UUIDs, and other
blockchain-related data formats.
"""

from uuid import UUID


def validate_solana_address(address: str) -> bool:
    """
    Validate Solana address format.

    Solana addresses are base58-encoded 32-byte public keys.
    Valid addresses are typically 32-44 characters.

    Args:
        address: Solana address string

    Returns:
        True if valid format, False otherwise

    Examples:
        >>> validate_solana_address("11111111111111111111111111111111")
        True
        >>> validate_solana_address("invalid")
        False
    """
    if not address or not isinstance(address, str):
        return False

    # Basic length check (base58 32 bytes = ~32-44 chars)
    if len(address) < 32 or len(address) > 44:
        return False

    # Check characters are valid base58
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if not all(c in base58_chars for c in address):
        return False

    return True


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format, False otherwise

    Examples:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> validate_uuid("invalid-uuid")
        False
    """
    try:
        UUID(uuid_str)
        return True
    except (ValueError, AttributeError, TypeError):
        return False
