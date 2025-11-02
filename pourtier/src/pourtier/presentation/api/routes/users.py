"""
User API routes.

Provides endpoints for user management:
- POST /users/ - Create new user
- GET /users/me - Get current authenticated user
- GET /users/{user_id} - Get user by ID
- GET /users/wallet/{wallet_address} - Get user by wallet address

Note: Escrow data (balance, account) available via GET /escrow/balance
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pourtier.application.use_cases.check_user_legal_compliance import (
    CheckUserLegalCompliance,
)
from pourtier.application.use_cases.create_user import CreateUser
from pourtier.application.use_cases.get_user_by_wallet import (
    GetUserByWallet,
    GetUserByWalletCommand,
)
from pourtier.application.use_cases.get_user_profile import (
    GetUserProfile,
    GetUserProfileCommand,
)
from pourtier.di.dependencies import (
    get_check_user_legal_compliance,
    get_create_user,
    get_get_user_by_wallet,
    get_get_user_profile,
)
from pourtier.domain.entities.user import User
from pourtier.domain.exceptions import EntityNotFoundError, ValidationError
from pourtier.infrastructure.auth.jwt_handler import extract_wallet_type
from pourtier.presentation.api.middleware.auth import get_current_user
from pourtier.presentation.schemas.legal_schemas import LegalDocumentResponse
from pourtier.presentation.schemas.user_schemas import (
    CreateUserRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Register new user with wallet address",
)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUser = Depends(get_create_user),
) -> UserResponse:
    """
    Create new user account.

    Args:
        request: Wallet address for new user
        use_case: CreateUser use case (injected)

    Returns:
        Created user details

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 500 if creation fails
    """
    try:
        user = await use_case.execute(
            wallet_address=request.wallet_address,
        )

        return UserResponse(
            id=str(user.id),
            wallet_address=user.wallet_address,
            wallet_type="Unknown",
            created_at=user.created_at,
            pending_documents=[],
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get authenticated user's profile with legal compliance status",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    compliance_use_case: CheckUserLegalCompliance = Depends(
        get_check_user_legal_compliance
    ),
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header.
    Includes pending legal documents that user needs to accept.

    Args:
        current_user: User from JWT token (injected by dependency)
        credentials: JWT token credentials
        compliance_use_case: Legal compliance use case (injected)

    Returns:
        Current user profile details with pending_documents

    Raises:
        HTTPException: 403 if authentication fails
    """
    # Extract wallet_type from JWT token
    token = credentials.credentials
    wallet_type = extract_wallet_type(token)

    # Check legal compliance
    _, pending_documents = await compliance_use_case.execute(current_user.id)

    # Convert domain entities to response schemas
    pending_docs_response = [
        LegalDocumentResponse(
            id=str(doc.id),
            document_type=doc.document_type,
            version=doc.version,
            title=doc.title,
            content=doc.content,
            status=doc.status,
            effective_date=doc.effective_date,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in pending_documents
    ]

    return UserResponse(
        id=str(current_user.id),
        wallet_address=current_user.wallet_address,
        wallet_type=wallet_type,
        created_at=current_user.created_at,
        pending_documents=pending_docs_response,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Retrieve user details by ID",
)
async def get_user_profile(
    user_id: UUID,
    use_case: GetUserProfile = Depends(get_get_user_profile),
) -> UserResponse:
    """
    Get user profile by ID.

    Args:
        user_id: User unique identifier
        use_case: GetUserProfile use case (injected)

    Returns:
        User profile details

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if retrieval fails
    """
    try:
        # Use command pattern for use case
        command = GetUserProfileCommand(user_id=user_id)
        user = await use_case.execute(command)

        return UserResponse(
            id=str(user.id),
            wallet_address=user.wallet_address,
            wallet_type="Unknown",
            created_at=user.created_at,
            pending_documents=[],
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.get(
    "/wallet/{wallet_address}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by wallet",
    description="Retrieve user details by wallet address",
)
async def get_user_by_wallet(
    wallet_address: str,
    use_case: GetUserByWallet = Depends(get_get_user_by_wallet),
) -> UserResponse:
    """
    Get user profile by wallet address.

    Args:
        wallet_address: Wallet address to lookup
        use_case: GetUserByWallet use case (injected)

    Returns:
        User profile details

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if retrieval fails
    """
    try:
        # Use command pattern for use case
        command = GetUserByWalletCommand(wallet_address=wallet_address)
        user = await use_case.execute(command)

        return UserResponse(
            id=str(user.id),
            wallet_address=user.wallet_address,
            wallet_type="Unknown",
            created_at=user.created_at,
            pending_documents=[],
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )
