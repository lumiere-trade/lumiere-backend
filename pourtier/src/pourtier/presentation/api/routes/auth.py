"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from pourtier.application.use_cases.create_user_with_legal import (
    CreateUserWithLegal,
)
from pourtier.application.use_cases.login_user import LoginUser
from pourtier.application.use_cases.verify_wallet_signature import (
    VerifyWalletSignature,
)
from pourtier.di.dependencies import (
    get_create_user_with_legal,
    get_login_user,
    get_verify_wallet_signature,
    get_wallet_authenticator,
)
from pourtier.domain.entities.user_legal_acceptance import AcceptanceMethod
from pourtier.domain.exceptions import EntityNotFoundError, ValidationError
from pourtier.domain.services.i_wallet_authenticator import IWalletAuthenticator
from pourtier.infrastructure.auth import jwt_handler
from pourtier.presentation.schemas.auth_schemas import (
    CreateAccountRequest,
    CreateAccountResponse,
    LoginRequest,
    LoginResponse,
    PendingDocumentInfo,
    VerifyWalletRequest,
    VerifyWalletResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================================================================
# Verify Wallet Endpoint
# ================================================================


@router.post(
    "/verify",
    response_model=VerifyWalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify wallet signature",
    description="Verify wallet ownership without creating user",
)
async def verify_wallet(
    request: VerifyWalletRequest,
    use_case: VerifyWalletSignature = Depends(get_verify_wallet_signature),
) -> VerifyWalletResponse:
    """
    Verify wallet signature and check if user exists.

    Flow:
    1. Verify signature against wallet address
    2. Check if user exists in database
    3. Return verification result

    Does NOT create user or generate JWT.
    """
    try:
        result = await use_case.execute(
            wallet_address=request.wallet_address,
            message=request.message,
            signature=request.signature,
        )

        return VerifyWalletResponse(
            signature_valid=result.signature_valid,
            user_exists=result.user_exists,
            user_id=str(result.user_id) if result.user_id else None,
            wallet_address=result.wallet_address,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


# ================================================================
# Create Account Endpoint
# ================================================================


@router.post(
    "/create-account",
    response_model=CreateAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create account with legal acceptance",
    description="Create new user and record legal document acceptance",
)
async def create_account(
    request: CreateAccountRequest,
    req: Request,
    use_case: CreateUserWithLegal = Depends(get_create_user_with_legal),
    wallet_authenticator: IWalletAuthenticator = Depends(get_wallet_authenticator),
) -> CreateAccountResponse:
    """
    Create new user account with legal acceptance.

    Flow:
    1. Verify wallet signature
    2. Verify user doesn't already exist
    3. Create user in database
    4. Record legal document acceptances
    5. Generate JWT token

    Requires acceptance of all active legal documents.
    """
    try:
        # 1. Verify signature first
        is_valid = await wallet_authenticator.verify_signature(
            wallet_address=request.wallet_address,
            message=request.message,
            signature=request.signature,
        )

        if not is_valid:
            raise ValidationError(
                field="signature",
                reason="Invalid wallet signature",
            )

        # 2. Extract IP and user agent from request
        ip_address = request.ip_address or req.client.host
        user_agent = request.user_agent or req.headers.get("user-agent")

        # 3. Create user with legal acceptance
        user = await use_case.execute(
            wallet_address=request.wallet_address,
            accepted_document_ids=request.accepted_documents,
            acceptance_method=AcceptanceMethod.WEB_CHECKBOX,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 4. Generate JWT token
        access_token = jwt_handler.create_access_token(
            user_id=user.id,
            wallet_address=user.wallet_address,
        )

        return CreateAccountResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            wallet_address=user.wallet_address,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account creation failed: {str(e)}",
        )


# ================================================================
# Login Endpoint
# ================================================================


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login existing user",
    description="Login user and check legal compliance",
)
async def login(
    request: LoginRequest,
    use_case: LoginUser = Depends(get_login_user),
) -> LoginResponse:
    """
    Login existing user.

    Flow:
    1. Verify wallet signature
    2. Get user from database
    3. Check legal compliance
    4. Generate JWT token if compliant
    5. Return pending documents if not compliant

    User can login even if not compliant, but should be prompted
    to accept pending documents.
    """
    try:
        result = await use_case.execute(
            wallet_address=request.wallet_address,
            message=request.message,
            signature=request.signature,
        )

        # Generate JWT token
        access_token = jwt_handler.create_access_token(
            user_id=result.user.id,
            wallet_address=result.user.wallet_address,
        )

        # Convert pending documents to response format
        pending_docs = [
            PendingDocumentInfo(
                id=str(doc.id),
                document_type=doc.document_type.value,
                version=doc.version,
                title=doc.title,
            )
            for doc in result.pending_documents
        ]

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(result.user.id),
            wallet_address=result.user.wallet_address,
            is_compliant=result.is_compliant,
            pending_documents=pending_docs,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )
