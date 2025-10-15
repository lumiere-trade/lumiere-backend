"""
Helper to sign messages with real Solana keypair.
"""

import json

import base58
from nacl.signing import SigningKey

from shared.blockchain.wallets import PlatformWallets


def load_keypair(keypair_path: str = None) -> SigningKey:
    """
    Load Solana keypair from JSON file.

    Args:
        keypair_path: Path to keypair JSON file.
                     Defaults to Alice test keypair from shared.tests

    Returns:
        SigningKey instance for signing operations
    """
    if keypair_path is None:
        keypair_path = PlatformWallets.get_test_alice_keypair()

    with open(keypair_path, "r") as f:
        keypair_data = json.load(f)

    # Keypair JSON is array of bytes [secret_key + public_key]
    # First 32 bytes is the secret key
    secret_key_bytes = bytes(keypair_data[:32])
    return SigningKey(secret_key_bytes)


def sign_message(message: str, keypair_path: str = None) -> str:
    """
    Sign a message with Solana keypair.

    Args:
        message: Message to sign
        keypair_path: Optional path to keypair. Defaults to Alice.

    Returns:
        Base58 encoded signature
    """
    signing_key = load_keypair(keypair_path)

    # Sign the message
    signature = signing_key.sign(message.encode())

    # Return base58 encoded signature
    return base58.b58encode(signature.signature).decode()


def get_wallet_address(keypair_path: str = None) -> str:
    """
    Get wallet address from keypair.

    Args:
        keypair_path: Optional path to keypair. Defaults to Alice.

    Returns:
        Base58 encoded public key (wallet address)
    """
    signing_key = load_keypair(keypair_path)
    public_key = signing_key.verify_key
    return base58.b58encode(bytes(public_key)).decode()


if __name__ == "__main__":
    # Test with Alice keypair
    wallet = get_wallet_address()
    print(f"Wallet: {wallet}")

    message = "test message"
    signature = sign_message(message)
    print(f"Signature: {signature}")
