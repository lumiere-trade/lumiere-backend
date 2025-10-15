"""
Cleanup escrows for test wallets.

Finds all escrows owned by user_* wallets, withdraws funds, and closes them.
"""

import base64
import json
import time
from pathlib import Path

import requests
import yaml
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction


def load_config(config_file: str) -> dict:
    """Load configuration file."""
    config_path = Path(__file__).parent.parent / "config" / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


def get_keypair(keypair_path: Path) -> Keypair:
    """Load keypair from file."""
    with open(keypair_path) as f:
        keypair_data = json.load(f)
        return Keypair.from_bytes(bytes(keypair_data))


def find_escrows_for_wallet(wallet_address: str, rpc_url: str, program_id: str) -> list:
    """
    Find all escrow accounts for a wallet.

    Args:
        wallet_address: Wallet public key
        rpc_url: Solana RPC URL
        program_id: Escrow program ID

    Returns:
        List of escrow addresses
    """
    client = Client(rpc_url)

    try:
        program_pubkey = Pubkey.from_string(program_id)
        response = client.get_program_accounts(program_pubkey, encoding="base64")

        escrows = []

        for account in response.value:
            try:
                # Parse account data
                data = account.account.data

                # User pubkey is at offset 8 (after discriminator)
                user_bytes = data[8:40]
                user_pubkey = Pubkey.from_bytes(bytes(user_bytes))

                if str(user_pubkey) == wallet_address:
                    escrows.append(str(account.pubkey))

            except Exception:
                # Skip accounts we can't parse
                continue

        return escrows

    except Exception as e:
        print(f"  Error finding escrows: {e}")
        return []


def sign_transaction(unsigned_tx_base64: str, keypair: Keypair) -> str:
    """Sign a transaction."""
    tx_bytes = base64.b64decode(unsigned_tx_base64)
    tx = Transaction.from_bytes(tx_bytes)
    tx.sign([keypair], tx.message.recent_blockhash)
    signed_tx_bytes = bytes(tx)
    return base64.b64encode(signed_tx_bytes).decode("utf-8")


def send_transaction(signed_tx_base64: str, bridge_url: str) -> str:
    """Send signed transaction."""
    response = requests.post(
        f"{bridge_url}/escrow/send-transaction",
        json={"signedTransaction": signed_tx_base64},
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Send failed: {response.text}")

    data = response.json()
    if not data.get("success"):
        raise Exception(f"Send failed: {data.get('error')}")

    return data["signature"]


def get_escrow_info(escrow_address: str, bridge_url: str) -> dict | None:
    """Get escrow info."""
    try:
        response = requests.get(f"{bridge_url}/escrow/{escrow_address}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        return None
    except Exception:
        return None


def get_escrow_balance(escrow_address: str, bridge_url: str) -> float:
    """Get escrow balance."""
    try:
        response = requests.get(
            f"{bridge_url}/escrow/balance/{escrow_address}", timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("balance", 0)
        return 0
    except Exception:
        return 0


def revoke_authority(keypair: Keypair, escrow_address: str, bridge_url: str) -> bool:
    """Revoke authority from escrow."""
    wallet = str(keypair.pubkey())

    print("    Revoking authority...")

    try:
        response = requests.post(
            f"{bridge_url}/escrow/prepare-revoke",
            json={"userWallet": wallet, "escrowAccount": escrow_address},
            timeout=30,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        if not data.get("success"):
            return False

        unsigned_tx = data["transaction"]
        signed_tx = sign_transaction(unsigned_tx, keypair)
        signature = send_transaction(signed_tx, bridge_url)

        print(f"    Revoked: {signature[:8]}...")
        time.sleep(5)  # Wait for confirmation
        return True

    except Exception as e:
        print(f"    Revoke failed: {e}")
        return False


def withdraw_funds(keypair: Keypair, escrow_address: str, bridge_url: str) -> bool:
    """Withdraw all funds from escrow."""
    wallet = str(keypair.pubkey())

    print("    Withdrawing funds...")

    try:
        response = requests.post(
            f"{bridge_url}/escrow/prepare-withdraw",
            json={"userWallet": wallet, "escrowAccount": escrow_address},
            timeout=30,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        if not data.get("success"):
            return False

        unsigned_tx = data["transaction"]
        signed_tx = sign_transaction(unsigned_tx, keypair)
        signature = send_transaction(signed_tx, bridge_url)

        print(f"    Withdrawn: {signature[:8]}...")
        time.sleep(5)  # Wait for confirmation
        return True

    except Exception as e:
        print(f"    Withdraw failed: {e}")
        return False


def close_escrow(keypair: Keypair, escrow_address: str, bridge_url: str) -> bool:
    """Close escrow account."""
    wallet = str(keypair.pubkey())

    print("    Closing escrow...")

    try:
        response = requests.post(
            f"{bridge_url}/escrow/prepare-close",
            json={"userWallet": wallet, "escrowAccount": escrow_address},
            timeout=30,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        if not data.get("success"):
            return False

        unsigned_tx = data["transaction"]
        signed_tx = sign_transaction(unsigned_tx, keypair)
        signature = send_transaction(signed_tx, bridge_url)

        print(f"    Closed: {signature[:8]}...")
        time.sleep(5)  # Wait for confirmation
        return True

    except Exception as e:
        print(f"    Close failed: {e}")
        return False


def cleanup_single_escrow(
    keypair: Keypair, escrow_address: str, bridge_url: str
) -> bool:
    """
    Cleanup a single escrow.

    Args:
        keypair: User keypair
        escrow_address: Escrow address
        bridge_url: Bridge URL

    Returns:
        True if successful
    """
    print(f"\n  Escrow: {escrow_address[:8]}...")

    # Get escrow info
    info = get_escrow_info(escrow_address, bridge_url)
    if not info:
        print("    Not found or already closed")
        return True

    # Check if active (has authority delegated)
    if info.get("isActive"):
        print("    Authority is active")
        if not revoke_authority(keypair, escrow_address, bridge_url):
            return False

    # Check balance
    balance = get_escrow_balance(escrow_address, bridge_url)
    print(f"    Balance: {balance}")

    if balance > 0:
        if not withdraw_funds(keypair, escrow_address, bridge_url):
            return False

    # Close escrow
    if not close_escrow(keypair, escrow_address, bridge_url):
        return False

    print("    Cleanup successful")
    return True


def cleanup_escrows(config_file: str, specific_wallet: str | None = None) -> bool:
    """
    Cleanup escrows for test wallets.

    Args:
        config_file: Config file name
        specific_wallet: Optional specific wallet name (e.g., "user_alice")

    Returns:
        True if successful
    """
    from cli.bridge import (
        check_bridge_status,
        get_bridge_url,
        start_bridge,
        stop_bridge,
    )

    # Load config
    try:
        config = load_config(config_file)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return False

    # Start bridge if not running
    bridge_was_running, bridge_url = check_bridge_status()

    if not bridge_was_running:
        print("Starting bridge...")
        if not start_bridge(config_file):
            print("Failed to start bridge")
            return False
        bridge_url = get_bridge_url(config)

    try:
        # Find keypairs
        keypairs_dir = Path.home() / "lumiere" / "keypairs" / "test"

        if not keypairs_dir.exists():
            print(f"Keypairs directory not found: {keypairs_dir}")
            return False

        # Filter keypairs
        if specific_wallet:
            user_keypairs = [keypairs_dir / f"{specific_wallet}.json"]
        else:
            user_keypairs = sorted(keypairs_dir.glob("user_*.json"))

        if not user_keypairs:
            print("No user keypairs found")
            return False

        print(f"\n📋 Found {len(user_keypairs)} wallet(s)")

        all_success = True

        for keypair_path in user_keypairs:
            if not keypair_path.exists():
                print(f"Keypair not found: {keypair_path}")
                all_success = False
                continue

            wallet_name = keypair_path.stem
            print(f"\n{'='*60}")
            print(f"👤 {wallet_name}")
            print(f"{'='*60}")

            keypair = get_keypair(keypair_path)
            wallet = str(keypair.pubkey())
            print(f"Address: {wallet}")

            # Find escrows
            print("🔍 Searching for escrows...")
            escrows = find_escrows_for_wallet(
                wallet, config["solana_rpc_url"], config["program_id"]
            )

            if not escrows:
                print("No escrows found")
                continue

            print(f"Found {len(escrows)} escrow(s)")

            for escrow in escrows:
                if not cleanup_single_escrow(keypair, escrow, bridge_url):
                    all_success = False

        return all_success

    finally:
        # Stop bridge if we started it
        if not bridge_was_running:
            print("\n🛑 Stopping bridge...")
            stop_bridge()
