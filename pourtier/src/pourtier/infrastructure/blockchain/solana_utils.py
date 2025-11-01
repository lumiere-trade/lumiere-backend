"""
Solana blockchain utilities.

Helper functions for working with Solana blockchain.
"""

from solders.pubkey import Pubkey


def derive_escrow_pda(user_wallet: str, program_id: str) -> tuple[str, int]:
    """
    Derive escrow PDA for user-based escrow (no strategy_id).

    Args:
        user_wallet: User wallet address (base58)
        program_id: Escrow program ID (base58)

    Returns:
        Tuple of (escrow_pda_address, bump_seed)

    Raises:
        ValueError: If addresses are invalid
    """
    try:
        user_pubkey = Pubkey.from_string(user_wallet)
        program_pubkey = Pubkey.from_string(program_id)

        seeds = [b"escrow", bytes(user_pubkey)]
        pda, bump = Pubkey.find_program_address(seeds, program_pubkey)

        return str(pda), bump

    except Exception as e:
        raise ValueError(f"Failed to derive escrow PDA: {e}")
