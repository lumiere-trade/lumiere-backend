"""
Transaction signer for Solana transactions.

Handles signing transactions with user keypairs for user-based escrow.
NO strategy_id - one escrow per user.
"""

from pathlib import Path
from typing import Optional, Tuple

import requests
from solana.rpc.api import Client
from solders.keypair import Keypair  # type: ignore
from solders.transaction import Transaction  # type: ignore


class TransactionSigner:
    """Sign and send Solana transactions for user-based escrow."""

    def __init__(self, bridge_url: str, keypair_path: str, rpc_url: str) -> None:
        """
        Initialize transaction signer.

        Args:
            bridge_url: Bridge server URL
            keypair_path: Path to user keypair JSON
            rpc_url: Solana RPC URL
        """
        self.bridge_url = bridge_url
        self.rpc_url = rpc_url

        # Load keypair
        keypair_file = Path(keypair_path).expanduser()
        with open(keypair_file, "r") as f:
            import json

            keypair_data = json.load(f)
            self.keypair = Keypair.from_bytes(bytes(keypair_data))

        self.client = Client(rpc_url)

    def prepare_and_sign_initialize(
        self,
        max_balance: Optional[int] = None,
    ) -> Tuple[str, str, str]:
        """
        Prepare, sign and send initialize escrow transaction.

        User-based escrow (NO strategy_id needed).

        Args:
            max_balance: Optional max balance limit

        Returns:
            Tuple of (escrow_account, signature, transaction_base64)
        """
        # Step 1: Prepare transaction
        payload = {
            "userWallet": str(self.keypair.pubkey()),
        }
        if max_balance is not None:
            payload["maxBalance"] = max_balance

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-initialize",
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare initialize failed: {response.status_code} - "
                f"{response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare initialize failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        escrow_account = data["escrowAccount"]

        # Step 2: Sign and send
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return escrow_account, signature, signed_tx_base64

    def prepare_and_sign_delegate_platform(
        self, escrow_account: str, authority: str
    ) -> Tuple[str, str]:
        """
        Prepare, sign and send delegate platform authority transaction.

        Args:
            escrow_account: Escrow account address
            authority: Platform authority address (Pourtier)

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-platform",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
                "authority": authority,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare delegate platform failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare delegate platform failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_delegate_trading(
        self, escrow_account: str, authority: str
    ) -> Tuple[str, str]:
        """
        Prepare, sign and send delegate trading authority transaction.

        Args:
            escrow_account: Escrow account address
            authority: Trading authority address (Chevalier)

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-delegate-trading",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
                "authority": authority,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare delegate trading failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare delegate trading failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_revoke_platform(self, escrow_account: str) -> Tuple[str, str]:
        """
        Prepare, sign and send revoke platform authority transaction.

        Args:
            escrow_account: Escrow account address

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-platform",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare revoke platform failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare revoke platform failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_revoke_trading(self, escrow_account: str) -> Tuple[str, str]:
        """
        Prepare, sign and send revoke trading authority transaction.

        Args:
            escrow_account: Escrow account address

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-revoke-trading",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare revoke trading failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare revoke trading failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_deposit(
        self, escrow_account: str, amount: float
    ) -> Tuple[str, str]:
        """
        Prepare, sign and send deposit transaction.

        Args:
            escrow_account: Escrow account address
            amount: Amount to deposit (in USDC)

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-deposit",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
                "amount": amount,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare deposit failed: " f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare deposit failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_withdraw(
        self, escrow_account: str, amount: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        Prepare, sign and send withdraw transaction.

        Args:
            escrow_account: Escrow account address
            amount: Amount to withdraw (None = withdraw all)

        Returns:
            Tuple of (signature, transaction_base64)
        """
        payload = {
            "userWallet": str(self.keypair.pubkey()),
            "escrowAccount": escrow_account,
        }
        if amount is not None:
            payload["amount"] = amount

        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-withdraw",
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare withdraw failed: " f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare withdraw failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def prepare_and_sign_close(self, escrow_account: str) -> Tuple[str, str]:
        """
        Prepare, sign and send close escrow transaction.

        Args:
            escrow_account: Escrow account address

        Returns:
            Tuple of (signature, transaction_base64)
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/prepare-close",
            json={
                "userWallet": str(self.keypair.pubkey()),
                "escrowAccount": escrow_account,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Prepare close failed: " f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Prepare close failed: {data.get('error')}")

        unsigned_tx_base64 = data["transaction"]
        signed_tx_base64 = self._sign_transaction(unsigned_tx_base64)
        signature = self._send_transaction(signed_tx_base64)

        return signature, signed_tx_base64

    def _sign_transaction(self, unsigned_tx_base64: str) -> str:
        """
        Sign transaction.

        Args:
            unsigned_tx_base64: Base64 encoded unsigned transaction

        Returns:
            Base64 encoded signed transaction
        """
        import base64

        tx_bytes = base64.b64decode(unsigned_tx_base64)
        tx = Transaction.from_bytes(tx_bytes)

        # Sign transaction
        tx.sign([self.keypair], tx.message.recent_blockhash)

        # Serialize signed transaction
        signed_tx_bytes = bytes(tx)
        signed_tx_base64 = base64.b64encode(signed_tx_bytes).decode("utf-8")

        return signed_tx_base64

    def _send_transaction(self, signed_tx_base64: str) -> str:
        """
        Send signed transaction.

        Args:
            signed_tx_base64: Base64 encoded signed transaction

        Returns:
            Transaction signature
        """
        response = requests.post(
            f"{self.bridge_url}/escrow/send-transaction",
            json={"signedTransaction": signed_tx_base64},
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"Send transaction failed: " f"{response.status_code} - {response.text}"
            )

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Send transaction failed: {data.get('error')}")

        return data["signature"]
