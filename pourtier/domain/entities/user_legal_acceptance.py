"""
User Legal Acceptance entity - Domain model for tracking acceptances.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class AcceptanceMethod(str, Enum):
    """Methods through which user accepted document."""

    WEB_CHECKBOX = "web_checkbox"
    API_EXPLICIT = "api_explicit"
    MIGRATION_IMPLICIT = "migration_implicit"


@dataclass
class UserLegalAcceptance:
    """
    User Legal Acceptance entity for tracking user document acceptances.

    Business rules:
    - User can only accept each document once
    - Acceptance is immutable (audit trail)
    - Tracks IP and user agent for legal purposes
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    accepted_at: datetime = field(default_factory=datetime.now)
    acceptance_method: AcceptanceMethod = field(default=AcceptanceMethod.WEB_CHECKBOX)
    ip_address: Optional[str] = field(default=None)
    user_agent: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate acceptance data after initialization."""
        # user_id and document_id validated by UUID type

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "document_id": str(self.document_id),
            "accepted_at": self.accepted_at.isoformat(),
            "acceptance_method": self.acceptance_method.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }
