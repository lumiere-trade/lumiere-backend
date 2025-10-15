"""
Solana blockchain client utilities.

Provides helper functions for signing and sending transactions.
"""

import json
from pathlib import Path
from typing import Optional

from solana.rpc.api import Client
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.transaction import Transaction


def load_keypair(keypair_path: str) -> Keypair:
    """
    Load Solana keypair from JSON file.

    Args:
        keypair_path: Path to keypair JSON file

    Returns:
        Solana Keypair object

    Examples:
        >>> keypair = load_keypair("~/lumiere/keypairs/test/user_alice.json")
        >>> print(keypair.pubkey())
    """
    path = Path(keypair_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Keypair not found: {keypair_path}")

    with open(path, "r") as f:
        secret_key = json.load(f)

    return Keypair.from_bytes(bytes(secret_key))


def get_keypair_address(keypair_path: str) -> str:
    """
    Get Solana address from keypair file.

    Args:
        keypair_path: Path to keypair JSON file

    Returns:
        Base58 encoded address string

    Examples:
        >>> address = get_keypair_address("~/lumiere/keypairs/test/user_alice.json")
    """
    keypair = load_keypair(keypair_path)
    return str(keypair.pubkey())


class SolanaClient:
    """
    Solana blockchain client for transaction signing and sending.

    Provides high-level interface for interacting with Solana RPC.
    """

    def __init__(self, rpc_url: str, keypair_path: Optional[str] = None):
        """
        Initialize Solana client.

        Args:
            rpc_url: Solana RPC endpoint URL
            keypair_path: Optional path to default keypair
        """
        self.client = Client(rpc_url)
        self.keypair = None

        if keypair_path:
            self.keypair = load_keypair(keypair_path)

    def get_balance(self, address: Optional[str] = None) -> float:
        """
        Get SOL balance for address.

        Args:
            address: Solana address (uses default keypair if None)

        Returns:
            Balance in SOL
        """
        if address is None and self.keypair is None:
            raise ValueError("No address or keypair provided")

        pubkey = Pubkey.from_string(address) if address else self.keypair.pubkey()
        response = self.client.get_balance(pubkey)

        # Convert lamports to SOL
        return response.value / 1_000_000_000

    def sign_transaction(self, transaction: Transaction) -> Transaction:
        """
        Sign transaction with keypair.

        Args:
            transaction: Unsigned Solana transaction

        Returns:
            Signed transaction
        """
        if self.keypair is None:
            raise ValueError("No keypair loaded for signing")

        transaction.sign(self.keypair)
        return transaction

    def send_transaction(
        self, transaction: Transaction, keypair: Optional[Keypair] = None
    ) -> str:
        """
        Sign and send transaction to Solana.

        Args:
            transaction: Transaction to send
            keypair: Optional keypair to use (uses default if None)

        Returns:
            Transaction signature

        Raises:
            Exception: If transaction fails
        """
        signer = keypair if keypair else self.keypair

        if signer is None:
            raise ValueError("No keypair provided for signing")

        # Sign transaction
        transaction.sign(signer)

        # Send transaction
        response = self.client.send_transaction(transaction)

        return str(response.value)
