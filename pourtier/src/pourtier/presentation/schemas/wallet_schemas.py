"""
API schemas for wallet operations.

Request and response models for wallet endpoints.
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    """
    Response schema for wallet balance query.

    Returns USDC balance in user's Solana wallet (not escrow).
    """

    wallet_address: str = Field(
        ...,
        description="Solana wallet address",
        example="kshy5yns5FGGXcFVfjT2fTzVsQLFnbZzL9zuh1ZKR2y",
    )
    balance: str = Field(
        ...,
        description="USDC balance (as string to preserve precision)",
        example="125.50",
    )
    token_mint: str = Field(
        ...,
        description="Token mint address",
        example="USDC",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Decimal: str,
        }
