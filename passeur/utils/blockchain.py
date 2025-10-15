"""
Blockchain utility functions for Passeur.

Provides helper functions for Solana blockchain operations like
UUID conversion, PDA seed derivation, and Anchor formatting.
"""

from typing import Tuple


def uuid_to_bytes(uuid_str: str) -> bytes:
    """
    Convert UUID string to 16-byte array.

    Args:
        uuid_str: UUID string (with or without dashes)

    Returns:
        16-byte bytes object

    Examples:
        >>> uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        >>> result = uuid_to_bytes(uuid_str)
        >>> len(result)
        16
    """
    # Remove dashes if present
    hex_str = uuid_str.replace("-", "")

    # Convert hex string to bytes
    return bytes.fromhex(hex_str)


def derive_escrow_pda_seeds(
    user_wallet: str, strategy_id: str
) -> Tuple[bytes, bytes, bytes]:
    """
    Get PDA derivation seeds for escrow account.

    Seeds: [b"escrow", user_pubkey_bytes, strategy_id_bytes]

    Args:
        user_wallet: User's Solana wallet address (base58)
        strategy_id: Strategy UUID string

    Returns:
        Tuple of (escrow_seed, user_bytes, strategy_bytes)

    Examples:
        >>> user = "11111111111111111111111111111111"
        >>> strategy = "550e8400-e29b-41d4-a716-446655440000"
        >>> seeds = derive_escrow_pda_seeds(user, strategy)
        >>> seeds[0]
        b'escrow'
    """
    escrow_seed = b"escrow"

    # User wallet is base58, decode to bytes
    try:
        import base58

        user_bytes = base58.b58decode(user_wallet)
    except ImportError:
        # Fallback for testing without base58 lib
        user_bytes = user_wallet.encode()[:32]

    # Strategy ID as bytes
    strategy_bytes = uuid_to_bytes(strategy_id)

    return (escrow_seed, user_bytes, strategy_bytes)


def format_uuid_for_anchor(uuid_str: str) -> list:
    """
    Format UUID as array for Anchor smart contract.

    Anchor expects UUID as array of 16 u8 integers.

    Args:
        uuid_str: UUID string

    Returns:
        List of 16 integers (0-255)

    Examples:
        >>> uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        >>> result = format_uuid_for_anchor(uuid_str)
        >>> len(result)
        16
        >>> all(0 <= x <= 255 for x in result)
        True
    """
    uuid_bytes = uuid_to_bytes(uuid_str)
    return list(uuid_bytes)
