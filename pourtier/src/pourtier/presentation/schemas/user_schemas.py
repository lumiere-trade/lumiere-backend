"""
User API schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    """Request to create new user - Web3 wallet only."""

    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana wallet address (base58)",
    )


class UserResponse(BaseModel):
    """User response with all details."""

    id: str
    wallet_address: str
    escrow_account: Optional[str] = None
    escrow_balance: Decimal
    escrow_token_mint: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class UpdateUserRequest(BaseModel):
    """Request to update user profile - minimal fields."""

    # Future: Add preferences, settings, etc. (non-identifying data)
