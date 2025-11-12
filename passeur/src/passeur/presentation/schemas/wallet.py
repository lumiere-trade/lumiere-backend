"""
Wallet operation schemas.

Mirrors Node.js bridge API contract for wallet queries.
"""

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    """
    Response from GET /wallet/balance.
    
    Returns wallet token balance.
    """
    
    success: bool = Field(..., description="Query success status")
    balance: float = Field(..., description="Balance in USDC (human-readable)")
    balanceLamports: str = Field(..., description="Balance in lamports (raw)")
    decimals: int = Field(..., description="Token decimals")
    tokenMint: str = Field(..., description="Token mint address")
    wallet: str = Field(..., description="Wallet public key")
