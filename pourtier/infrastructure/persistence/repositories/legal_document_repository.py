"""
Legal Document repository implementation.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.infrastructure.persistence.models import LegalDocumentModel


class LegalDocumentRepository(ILegalDocumentRepository):
    """SQLAlchemy implementation of legal document repository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, document: LegalDocument) -> LegalDocument:
        """
        Create new legal document in database.

        Args:
            document: LegalDocument entity to create

        Returns:
            Created legal document entity
        """
        model = LegalDocumentModel(
            id=document.id,
            document_type=document.document_type.value,
            version=document.version,
            title=document.title,
            content=document.content,
            status=document.status.value,
            effective_date=document.effective_date,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get_by_id(self, document_id: UUID) -> Optional[LegalDocument]:
        """
        Get legal document by ID.

        Args:
            document_id: Document unique identifier

        Returns:
            LegalDocument entity if found, None otherwise
        """
        stmt = select(LegalDocumentModel).where(LegalDocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_by_type_and_version(
        self,
        document_type: DocumentType,
        version: str,
    ) -> Optional[LegalDocument]:
        """
        Get legal document by type and version.

        Args:
            document_type: Type of document (TOS, Privacy Policy)
            version: Document version string

        Returns:
            LegalDocument entity if found, None otherwise
        """
        stmt = select(LegalDocumentModel).where(
            LegalDocumentModel.document_type == document_type.value,
            LegalDocumentModel.version == version,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_active_by_type(
        self, document_type: DocumentType
    ) -> Optional[LegalDocument]:
        """
        Get active legal document by type.

        Args:
            document_type: Type of document (TOS, Privacy Policy)

        Returns:
            Active LegalDocument entity if found, None otherwise
        """
        stmt = (
            select(LegalDocumentModel)
            .where(
                LegalDocumentModel.document_type == document_type.value,
                LegalDocumentModel.status == DocumentStatus.ACTIVE.value,
            )
            .order_by(LegalDocumentModel.effective_date.desc())
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_all_active(self) -> List[LegalDocument]:
        """
        Get all active legal documents.

        Returns:
            List of active LegalDocument entities
        """
        stmt = (
            select(LegalDocumentModel)
            .where(LegalDocumentModel.status == DocumentStatus.ACTIVE.value)
            .order_by(
                LegalDocumentModel.document_type,
                LegalDocumentModel.effective_date.desc(),
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def update(self, document: LegalDocument) -> LegalDocument:
        """
        Update existing legal document.

        Args:
            document: LegalDocument entity with updated data

        Returns:
            Updated legal document entity
        """
        stmt = select(LegalDocumentModel).where(LegalDocumentModel.id == document.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Legal document {document.id} not found")

        # Update fields
        model.document_type = document.document_type.value
        model.version = document.version
        model.title = document.title
        model.content = document.content
        model.status = document.status.value
        model.effective_date = document.effective_date
        model.updated_at = document.updated_at

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, document_id: UUID) -> bool:
        """
        Delete legal document by ID.

        Args:
            document_id: Document unique identifier

        Returns:
            True if deleted, False if not found
        """
        stmt = select(LegalDocumentModel).where(LegalDocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()

        return True

    def _to_entity(self, model: LegalDocumentModel) -> LegalDocument:
        """
        Convert LegalDocumentModel to LegalDocument entity.

        Args:
            model: SQLAlchemy model

        Returns:
            LegalDocument domain entity
        """
        return LegalDocument(
            id=model.id,
            document_type=DocumentType(model.document_type),
            version=model.version,
            title=model.title,
            content=model.content,
            status=DocumentStatus(model.status),
            effective_date=model.effective_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
