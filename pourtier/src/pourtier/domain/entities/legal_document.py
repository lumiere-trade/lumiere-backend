"""
Legal Document entity - Domain model for legal documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    """Types of legal documents."""

    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"


class DocumentStatus(str, Enum):
    """Document lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class LegalDocument:
    """
    Legal Document entity representing platform legal documents.

    Business rules:
    - Only one active document per type at a time
    - Documents can be versioned
    - Draft documents are not shown to users
    - Archived documents are kept for audit trail
    """

    id: UUID = field(default_factory=uuid4)
    document_type: DocumentType = field(default=DocumentType.TERMS_OF_SERVICE)
    version: str = field(default="1.0.0")
    title: str = field(default="")
    content: str = field(default="")
    status: DocumentStatus = field(default=DocumentStatus.DRAFT)
    effective_date: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate legal document data after initialization."""
        if not self.title:
            raise ValueError("Document title is required")

        if not self.content:
            raise ValueError("Document content is required")

        if not self.version:
            raise ValueError("Document version is required")

    def activate(self) -> None:
        """
        Activate document (make it visible to users).

        Raises:
            ValueError: If effective_date not set
        """
        if not self.effective_date:
            raise ValueError("Effective date required to activate document")

        self.status = DocumentStatus.ACTIVE
        self.updated_at = datetime.now()

    def archive(self) -> None:
        """Archive document (keep for audit, hide from users)."""
        self.status = DocumentStatus.ARCHIVED
        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """Check if document is currently active."""
        if self.status != DocumentStatus.ACTIVE:
            return False

        if self.effective_date and datetime.now() < self.effective_date:
            return False

        return True

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "document_type": self.document_type.value,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "status": self.status.value,
            "effective_date": (
                self.effective_date.isoformat() if self.effective_date else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
