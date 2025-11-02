"""
User API schemas.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from pourtier.presentation.schemas.legal_schemas import LegalDocumentResponse


class CreateUserRequest(BaseModel):
    """Request to create new user - Web3 wallet only."""

    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana wallet address (base58)",
    )


class UserResponse(BaseModel):
    """
    User response - minimal immutable identity.
    
    Architecture decision:
    - User entity is minimal Web3 identity
    - Escrow data queried separately via GET /escrow/balance
    - Clean separation: User routes = user data, Escrow routes = escrow data
    """

    id: str
    wallet_address: str
    wallet_type: str = Field(
        default="Unknown",
        description="Wallet application type (Phantom, Solflare, etc.)",
    )
    created_at: datetime
    pending_documents: List[LegalDocumentResponse] = Field(
        default=[],
        description="Legal documents user hasn't accepted yet",
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class UpdateUserRequest(BaseModel):
    """Request to update user profile - minimal fields."""

    # Future: Add preferences, settings, etc. (non-identifying data)
