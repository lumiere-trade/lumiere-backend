"""
Authentication API schemas.
"""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ================================================================
# Verify Wallet Schemas
# ================================================================


class VerifyWalletRequest(BaseModel):
    """Request to verify wallet signature."""

    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana wallet address",
    )
    signature: str = Field(..., description="Signed message (base58 encoded)")
    message: str = Field(..., description="Original message that was signed")


class VerifyWalletResponse(BaseModel):
    """Response from wallet verification."""

    signature_valid: bool = Field(..., description="Signature is valid")
    user_exists: bool = Field(..., description="User exists in database")
    user_id: Optional[str] = Field(None, description="User ID if exists")
    wallet_address: str = Field(..., description="Wallet address")


# ================================================================
# Create Account Schemas
# ================================================================


class CreateAccountRequest(BaseModel):
    """Request to create new account with legal acceptance."""

    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana wallet address",
    )
    signature: str = Field(..., description="Signed message (base58 encoded)")
    message: str = Field(..., description="Original message that was signed")
    wallet_type: str = Field(
        default="Unknown",
        max_length=50,
        description="Wallet application type (Phantom, Backpack, etc.)",
    )
    accepted_documents: List[UUID] = Field(
        ...,
        description="List of document IDs being accepted",
        min_items=1,
    )
    ip_address: Optional[str] = Field(None, description="User IP address (for audit)")
    user_agent: Optional[str] = Field(None, description="User agent (for audit)")


class CreateAccountResponse(BaseModel):
    """Response from account creation."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    user_id: str = Field(..., description="Created user ID")
    wallet_address: str = Field(..., description="Wallet address")


# ================================================================
# Login Schemas
# ================================================================


class LoginRequest(BaseModel):
    """Request to login existing user."""

    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana wallet address",
    )
    signature: str = Field(..., description="Signed message (base58 encoded)")
    message: str = Field(..., description="Original message that was signed")
    wallet_type: str = Field(
        default="Unknown",
        max_length=50,
        description="Wallet application type (Phantom, Backpack, etc.)",
    )


class PendingDocumentInfo(BaseModel):
    """Information about pending legal document."""

    id: str
    document_type: str
    version: str
    title: str


class LoginResponse(BaseModel):
    """Response from user login."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    user_id: str = Field(..., description="User ID")
    wallet_address: str = Field(..., description="Wallet address")
    is_compliant: bool = Field(..., description="User has accepted all legal documents")
    pending_documents: List[PendingDocumentInfo] = Field(
        default_factory=list,
        description="Legal documents requiring acceptance",
    )
