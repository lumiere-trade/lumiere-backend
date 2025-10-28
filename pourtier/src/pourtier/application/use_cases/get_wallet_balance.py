"""
Get Wallet Balance use case.

Retrieves user's USDC balance from their Solana wallet (not escrow).
"""

from dataclasses import dataclass
from decimal import Decimal

from pourtier.domain.exceptions.base import ValidationError
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge


@dataclass
class WalletBalanceResult:
    """
    Result of wallet balance query.

    Attributes:
        wallet_address: User's Solana wallet address
        balance: USDC balance in wallet
        token_mint: USDC token mint address
    """

    wallet_address: str
    balance: Decimal
    token_mint: str


class GetWalletBalance:
    """
    Get user's wallet USDC balance.

    Business rules:
    - Queries Passeur Bridge which queries Solana RPC
    - Returns actual wallet balance, not escrow balance
    - Used for deposit modal "Available" display
    """

    def __init__(self, passeur_bridge: IPasseurBridge):
        """
        Initialize use case with dependencies.

        Args:
            passeur_bridge: Bridge service for querying Passeur
        """
        self.passeur_bridge = passeur_bridge

    async def execute(self, wallet_address: str) -> WalletBalanceResult:
        """
        Execute get wallet balance.

        Args:
            wallet_address: Solana wallet address to query

        Returns:
            WalletBalanceResult with balance

        Raises:
            ValidationError: If wallet address invalid
            BridgeError: If Passeur Bridge call fails
        """
        if not wallet_address or len(wallet_address) < 32:
            raise ValidationError("Invalid wallet address")

        balance = await self.passeur_bridge.get_wallet_balance(wallet_address)

        return WalletBalanceResult(
            wallet_address=wallet_address,
            balance=balance,
            token_mint="USDC",
        )
