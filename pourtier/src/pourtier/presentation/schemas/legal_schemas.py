"""
Legal API schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LegalDocumentResponse(BaseModel):
    """Legal document response."""

    id: str
    document_type: str
    version: str
    title: str
    content: str
    status: str
    effective_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class AcceptLegalDocumentsRequest(BaseModel):
    """Request to accept legal documents."""

    document_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of document IDs to accept (UUIDs)",
    )
    acceptance_method: str = Field(
        default="web_checkbox",
        description="Method: web_checkbox, api_explicit, migration_implicit",
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="User IP address (for audit trail)",
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string (for audit trail)",
    )


class UserLegalAcceptanceResponse(BaseModel):
    """User legal acceptance response."""

    id: str
    user_id: str
    document_id: str
    accepted_at: datetime
    acceptance_method: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class LegalComplianceResponse(BaseModel):
    """Legal compliance status response."""

    is_compliant: bool = Field(
        ...,
        description="True if user accepted all required documents",
    )
    pending_documents: List[LegalDocumentResponse] = Field(
        default=[],
        description="Documents user hasn't accepted yet",
    )
    accepted_count: int = Field(
        ...,
        description="Number of documents user has accepted",
    )
    total_required: int = Field(
        ...,
        description="Total number of required documents",
    )


class AcceptLegalDocumentsResponse(BaseModel):
    """Response after accepting legal documents."""

    success: bool
    acceptances: List[UserLegalAcceptanceResponse]
    message: str = Field(
        default="Legal documents accepted successfully",
    )
