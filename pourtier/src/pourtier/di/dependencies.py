"""
FastAPI dependency injection.

Provides dependencies for FastAPI routes using the DI container.
All dependencies are async-compatible and use proper scoping.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.config.settings import get_settings
from pourtier.di.container import get_container

# ================================================================
# Database Dependencies
# ================================================================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Yields async database session from container.
    Session is automatically closed after request.
    """
    container = get_container()
    async with container.database.session() as session:
        yield session


# ================================================================
# Service Dependencies
# ================================================================


def get_wallet_authenticator():
    """Get WalletAuthenticator service dependency."""
    container = get_container()
    return container.get_wallet_authenticator()


def get_passeur_bridge():
    """Get PasseurBridge service dependency."""
    container = get_container()
    return container.passeur_bridge


def get_escrow_query_service():
    """Get EscrowQueryService dependency."""
    container = get_container()
    return container.escrow_query_service


def get_idempotency_store():
    """Get IdempotencyStore dependency (optional)."""
    container = get_container()
    return container.idempotency_store


def get_program_id() -> str:
    """Get Solana escrow program ID from settings."""
    return get_settings().ESCROW_PROGRAM_ID


# ================================================================
# Use Case Dependencies
# ================================================================


def get_create_user(
    session: AsyncSession = Depends(get_db_session),
):
    """Get CreateUser use case dependency."""
    from pourtier.application.use_cases.create_user import CreateUser

    container = get_container()
    user_repo = container.get_user_repository(session)
    return CreateUser(user_repository=user_repo)


def get_get_user_profile(
    session: AsyncSession = Depends(get_db_session),
):
    """Get GetUserProfile use case dependency."""
    from pourtier.application.use_cases.get_user_profile import GetUserProfile

    container = get_container()
    user_repo = container.get_user_repository(session)
    return GetUserProfile(user_repository=user_repo)


def get_get_user_by_wallet(
    session: AsyncSession = Depends(get_db_session),
):
    """Get GetUserByWallet use case dependency."""
    from pourtier.application.use_cases.get_user_by_wallet import GetUserByWallet

    container = get_container()
    user_repo = container.get_user_repository(session)
    return GetUserByWallet(user_repository=user_repo)


def get_create_user_with_legal(
    session: AsyncSession = Depends(get_db_session),
):
    """Get CreateUserWithLegal use case dependency."""
    from pourtier.application.use_cases.create_user_with_legal import (
        CreateUserWithLegal,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)
    legal_doc_repo = container.get_legal_document_repository(session)
    user_legal_repo = container.get_user_legal_acceptance_repository(session)

    return CreateUserWithLegal(
        user_repository=user_repo,
        legal_document_repository=legal_doc_repo,
        user_legal_acceptance_repository=user_legal_repo,
    )


def get_login_user(
    session: AsyncSession = Depends(get_db_session),
    wallet_auth=Depends(get_wallet_authenticator),
):
    """Get LoginUser use case dependency."""
    from pourtier.application.use_cases.login_user import LoginUser

    container = get_container()
    user_repo = container.get_user_repository(session)
    legal_doc_repo = container.get_legal_document_repository(session)
    user_legal_repo = container.get_user_legal_acceptance_repository(session)

    return LoginUser(
        user_repository=user_repo,
        legal_document_repository=legal_doc_repo,
        user_legal_acceptance_repository=user_legal_repo,
        wallet_authenticator=wallet_auth,
    )


def get_verify_wallet_signature(
    session: AsyncSession = Depends(get_db_session),
    wallet_auth=Depends(get_wallet_authenticator),
):
    """Get VerifyWalletSignature use case dependency."""
    from pourtier.application.use_cases.verify_wallet_signature import (
        VerifyWalletSignature,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)

    return VerifyWalletSignature(
        user_repository=user_repo,
        wallet_authenticator=wallet_auth,
    )


def get_initialize_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    idempotency_store=Depends(get_idempotency_store),
    program_id: str = Depends(get_program_id),
):
    """Get InitializeEscrow use case dependency."""
    from pourtier.application.use_cases.initialize_escrow import InitializeEscrow

    container = get_container()
    user_repo = container.get_user_repository(session)
    escrow_tx_repo = container.get_escrow_transaction_repository(session)

    return InitializeEscrow(
        user_repository=user_repo,
        escrow_transaction_repository=escrow_tx_repo,
        passeur_bridge=passeur_bridge,
        program_id=program_id,
        idempotency_store=idempotency_store,
    )


def get_deposit_to_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    escrow_query_service=Depends(get_escrow_query_service),
    idempotency_store=Depends(get_idempotency_store),
    program_id: str = Depends(get_program_id),
):
    """Get DepositToEscrow use case dependency."""
    from pourtier.application.use_cases.deposit_to_escrow import DepositToEscrow

    container = get_container()
    user_repo = container.get_user_repository(session)
    escrow_tx_repo = container.get_escrow_transaction_repository(session)

    return DepositToEscrow(
        user_repository=user_repo,
        escrow_transaction_repository=escrow_tx_repo,
        passeur_bridge=passeur_bridge,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
        idempotency_store=idempotency_store,
    )


def get_withdraw_from_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    escrow_query_service=Depends(get_escrow_query_service),
    idempotency_store=Depends(get_idempotency_store),
    program_id: str = Depends(get_program_id),
):
    """Get WithdrawFromEscrow use case dependency."""
    from pourtier.application.use_cases.withdraw_from_escrow import (
        WithdrawFromEscrow,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)
    escrow_tx_repo = container.get_escrow_transaction_repository(session)

    return WithdrawFromEscrow(
        user_repository=user_repo,
        escrow_transaction_repository=escrow_tx_repo,
        passeur_bridge=passeur_bridge,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
        idempotency_store=idempotency_store,
    )


def get_get_escrow_balance(
    session: AsyncSession = Depends(get_db_session),
    escrow_query_service=Depends(get_escrow_query_service),
    program_id: str = Depends(get_program_id),
):
    """Get GetEscrowBalance use case dependency."""
    from pourtier.application.use_cases.get_escrow_balance import GetEscrowBalance

    container = get_container()
    user_repo = container.get_user_repository(session)

    return GetEscrowBalance(
        user_repository=user_repo,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
    )


def get_get_wallet_balance(
    passeur_bridge=Depends(get_passeur_bridge),
):
    """Get GetWalletBalance use case dependency."""
    from pourtier.application.use_cases.get_wallet_balance import GetWalletBalance

    return GetWalletBalance(
        passeur_bridge=passeur_bridge,
    )


def get_prepare_initialize_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    escrow_query_service=Depends(get_escrow_query_service),
    program_id: str = Depends(get_program_id),
):
    """Get PrepareInitializeEscrow use case dependency."""
    from pourtier.application.use_cases.prepare_initialize_escrow import (
        PrepareInitializeEscrow,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)

    return PrepareInitializeEscrow(
        user_repository=user_repo,
        passeur_bridge=passeur_bridge,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
    )


def get_prepare_deposit_to_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    escrow_query_service=Depends(get_escrow_query_service),
    program_id: str = Depends(get_program_id),
):
    """Get PrepareDepositToEscrow use case dependency."""
    from pourtier.application.use_cases.prepare_deposit_to_escrow import (
        PrepareDepositToEscrow,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)

    return PrepareDepositToEscrow(
        user_repository=user_repo,
        passeur_bridge=passeur_bridge,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
    )


def get_prepare_withdraw_from_escrow(
    session: AsyncSession = Depends(get_db_session),
    passeur_bridge=Depends(get_passeur_bridge),
    escrow_query_service=Depends(get_escrow_query_service),
    program_id: str = Depends(get_program_id),
):
    """Get PrepareWithdrawFromEscrow use case dependency."""
    from pourtier.application.use_cases.prepare_withdraw_from_escrow import (
        PrepareWithdrawFromEscrow,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)

    return PrepareWithdrawFromEscrow(
        user_repository=user_repo,
        passeur_bridge=passeur_bridge,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
    )


def get_create_subscription(
    session: AsyncSession = Depends(get_db_session),
    escrow_query_service=Depends(get_escrow_query_service),
    program_id: str = Depends(get_program_id),
):
    """Get CreateSubscription use case dependency."""
    from pourtier.application.use_cases.create_subscription import (
        CreateSubscription,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)
    subscription_repo = container.get_subscription_repository(session)

    return CreateSubscription(
        user_repository=user_repo,
        subscription_repository=subscription_repo,
        escrow_query_service=escrow_query_service,
        program_id=program_id,
    )


def get_get_active_legal_documents(
    session: AsyncSession = Depends(get_db_session),
):
    """Get GetActiveLegalDocuments use case dependency."""
    from pourtier.application.use_cases.get_active_legal_documents import (
        GetActiveLegalDocuments,
    )

    container = get_container()
    legal_doc_repo = container.get_legal_document_repository(session)
    return GetActiveLegalDocuments(legal_document_repository=legal_doc_repo)


def get_check_user_legal_compliance(
    session: AsyncSession = Depends(get_db_session),
):
    """Get CheckUserLegalCompliance use case dependency."""
    from pourtier.application.use_cases.check_user_legal_compliance import (
        CheckUserLegalCompliance,
    )

    container = get_container()
    user_repo = container.get_user_repository(session)
    legal_doc_repo = container.get_legal_document_repository(session)
    user_legal_repo = container.get_user_legal_acceptance_repository(session)

    return CheckUserLegalCompliance(
        user_repository=user_repo,
        legal_document_repository=legal_doc_repo,
        user_legal_acceptance_repository=user_legal_repo,
    )


def get_accept_legal_documents(
    session: AsyncSession = Depends(get_db_session),
):
    """Get AcceptLegalDocuments use case dependency."""
    from pourtier.application.use_cases.accept_legal_documents import (
        AcceptLegalDocuments,
    )

    container = get_container()
    legal_doc_repo = container.get_legal_document_repository(session)
    user_legal_repo = container.get_user_legal_acceptance_repository(session)
    user_repo = container.get_user_repository(session)

    return AcceptLegalDocuments(
        legal_document_repository=legal_doc_repo,
        user_legal_acceptance_repository=user_legal_repo,
        user_repository=user_repo,
    )
