"""
Escrow helper functions for testing and operations.

Provides utilities for checking escrow existence, deriving PDAs, etc.
"""

from solders.pubkey import Pubkey  # type: ignore


def derive_escrow_pda(user_address: str, strategy_id: str, program_id: str) -> Pubkey:
    """
    Derive escrow PDA address.

    Args:
        user_address: User wallet address
        strategy_id: Strategy UUID (with or without dashes)
        program_id: Escrow program ID

    Returns:
        Escrow PDA address

    Examples:
        >>> pda = derive_escrow_pda(
        ...     "8FimJHx8b4G3uqX2Fr7rVFRqLhHamqBDD6wug65LAiDz",
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     "9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS"
        ... )
    """
    user_pubkey = Pubkey.from_string(user_address)
    program_pubkey = Pubkey.from_string(program_id)

    # Remove dashes from UUID
    strategy_bytes = bytes.fromhex(strategy_id.replace("-", ""))

    # Derive PDA: [b"escrow", user_pubkey, strategy_id_bytes]
    seeds = [b"escrow", bytes(user_pubkey), strategy_bytes]

    pda, bump = Pubkey.find_program_address(seeds, program_pubkey)

    return pda


def check_escrow_exists(escrow_address: str, rpc_url: str) -> bool:
    """
    Check if escrow account exists on-chain.

    Args:
        escrow_address: Escrow account address
        rpc_url: Solana RPC URL

    Returns:
        True if account exists, False otherwise
    """
    from solana.rpc.api import Client

    client = Client(rpc_url)
    pubkey = Pubkey.from_string(escrow_address)

    try:
        account_info = client.get_account_info(pubkey)
        return account_info.value is not None
    except Exception:
        return False
