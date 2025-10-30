"""
Legal API routes.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from pourtier.application.use_cases.accept_legal_documents import (
    AcceptLegalDocuments,
)
from pourtier.application.use_cases.check_user_legal_compliance import (
    CheckUserLegalCompliance,
)
from pourtier.application.use_cases.get_active_legal_documents import (
    GetActiveLegalDocuments,
)
from pourtier.di.dependencies import (
    get_accept_legal_documents,
    get_check_user_legal_compliance,
    get_get_active_legal_documents,
)
from pourtier.domain.entities.user import User
from pourtier.domain.entities.user_legal_acceptance import (
    AcceptanceMethod,
)
from pourtier.domain.exceptions import EntityNotFoundError
from pourtier.infrastructure.cache import cache_response
from pourtier.presentation.api.middleware.auth import get_current_user
from pourtier.presentation.schemas.legal_schemas import (
    AcceptLegalDocumentsRequest,
    AcceptLegalDocumentsResponse,
    LegalComplianceResponse,
    LegalDocumentResponse,
    UserLegalAcceptanceResponse,
)

router = APIRouter(prefix="/legal", tags=["Legal"])


@router.get(
    "/documents",
    response_model=List[LegalDocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active legal documents",
    description="Retrieve all active legal documents (public endpoint)",
)
@cache_response(ttl=3600, key_prefix="legal:documents")
async def get_active_legal_documents(
    request: Request,
    use_case: GetActiveLegalDocuments = Depends(get_get_active_legal_documents),
) -> List[LegalDocumentResponse]:
    """
    Get all active legal documents.

    Public endpoint - no authentication required.
    Returns all documents users must accept.
    Cached for 1 hour (legal docs change rarely).

    Args:
        request: FastAPI request (for caching)

    Returns:
        List of active legal documents
    """
    try:
        documents = await use_case.execute()

        return [
            LegalDocumentResponse(
                id=str(doc.id),
                document_type=doc.document_type.value,
                version=doc.version,
                title=doc.title,
                content=doc.content,
                status=doc.status.value,
                effective_date=doc.effective_date,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get legal documents: {str(e)}",
        )


@router.post(
    "/accept",
    response_model=AcceptLegalDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept legal documents",
    description="Record user acceptance of legal documents (auth required)",
)
async def accept_legal_documents(
    request_body: AcceptLegalDocumentsRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    use_case: AcceptLegalDocuments = Depends(get_accept_legal_documents),
) -> AcceptLegalDocumentsResponse:
    """
    Accept legal documents.

    Requires authentication. Records acceptance with audit trail
    (IP address, user agent, timestamp).

    Args:
        request_body: Document IDs to accept
        http_request: FastAPI request object (for IP/user agent)
        current_user: Authenticated user from JWT

    Returns:
        Acceptance confirmation
    """
    try:
        # Parse document IDs
        document_ids = [UUID(doc_id) for doc_id in request_body.document_ids]

        # Parse acceptance method
        acceptance_method = AcceptanceMethod(request_body.acceptance_method)

        # Get IP address from request
        ip_address = (
            request_body.ip_address or http_request.client.host
            if http_request.client
            else None
        )

        # Get user agent from request
        user_agent = request_body.user_agent or http_request.headers.get("user-agent")

        # Execute use case
        acceptances = await use_case.execute(
            user_id=current_user.id,
            document_ids=document_ids,
            acceptance_method=acceptance_method,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AcceptLegalDocumentsResponse(
            success=True,
            acceptances=[
                UserLegalAcceptanceResponse(
                    id=str(acc.id),
                    user_id=str(acc.user_id),
                    document_id=str(acc.document_id),
                    accepted_at=acc.accepted_at,
                    acceptance_method=acc.acceptance_method.value,
                    ip_address=acc.ip_address,
                    user_agent=acc.user_agent,
                    created_at=acc.created_at,
                )
                for acc in acceptances
            ],
            message=(f"Successfully accepted {len(acceptances)} " f"legal document(s)"),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept legal documents: {str(e)}",
        )


@router.get(
    "/compliance",
    response_model=LegalComplianceResponse,
    status_code=status.HTTP_200_OK,
    summary="Check legal compliance",
    description="Check if user accepted all required documents (auth)",
)
@cache_response(ttl=300, key_prefix="legal:compliance")
async def check_legal_compliance(
    request: Request,
    current_user: User = Depends(get_current_user),
    compliance_use_case: CheckUserLegalCompliance = Depends(
        get_check_user_legal_compliance
    ),
    active_docs_use_case: GetActiveLegalDocuments = Depends(
        get_get_active_legal_documents
    ),
) -> LegalComplianceResponse:
    """
    Check user's legal compliance status.

    Requires authentication. Returns whether user has accepted
    all required documents and list of pending ones.
    Cached for 5 minutes per user.

    Args:
        request: FastAPI request (for caching)
        current_user: Authenticated user from JWT
        compliance_use_case: Check compliance use case (injected)
        active_docs_use_case: Get active documents use case (injected)

    Returns:
        Compliance status and pending documents
    """
    try:
        is_compliant, pending_documents = await compliance_use_case.execute(
            user_id=current_user.id
        )

        # Get total required documents
        all_active = await active_docs_use_case.execute()
        total_required = len(all_active)
        accepted_count = total_required - len(pending_documents)

        return LegalComplianceResponse(
            is_compliant=is_compliant,
            pending_documents=[
                LegalDocumentResponse(
                    id=str(doc.id),
                    document_type=doc.document_type.value,
                    version=doc.version,
                    title=doc.title,
                    content=doc.content,
                    status=doc.status.value,
                    effective_date=doc.effective_date,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                for doc in pending_documents
            ],
            accepted_count=accepted_count,
            total_required=total_required,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compliance: {str(e)}",
        )
