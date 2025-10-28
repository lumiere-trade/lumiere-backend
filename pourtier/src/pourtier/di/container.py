"""
Dependency Injection Container for Pourtier.

Manages all service instances and their dependencies.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from pourtier.application.use_cases.authenticate_wallet import (
    AuthenticateWallet,
)
from pourtier.application.use_cases.check_subscription_status import (
    CheckSubscriptionStatus,
)
from pourtier.application.use_cases.create_subscription import (
    CreateSubscription,
)
from pourtier.application.use_cases.create_user import CreateUser
from pourtier.application.use_cases.get_user_profile import GetUserProfile
from pourtier.application.use_cases.update_user_profile import (
    UpdateUserProfile,
)
from pourtier.config.settings import get_settings
from pourtier.domain.repositories.i_escrow_transaction_repository import (
    IEscrowTransactionRepository,
)
from pourtier.domain.repositories.i_legal_document_repository import (
    ILegalDocumentRepository,
)
from pourtier.domain.repositories.i_subscription_repository import (
    ISubscriptionRepository,
)
from pourtier.domain.repositories.i_user_legal_acceptance_repository import (
    IUserLegalAcceptanceRepository,
)
from pourtier.domain.repositories.i_user_repository import IUserRepository
from pourtier.domain.services.i_blockchain_verifier import (
    IBlockchainVerifier,
)
from pourtier.domain.services.i_escrow_contract_client import (
    IEscrowContractClient,
)
from pourtier.domain.services.i_escrow_query_service import (
    IEscrowQueryService,
)
from pourtier.domain.services.i_event_publisher import IEventPublisher
from pourtier.domain.services.i_passeur_bridge import IPasseurBridge
from pourtier.domain.services.i_wallet_authenticator import (
    IWalletAuthenticator,
)
from pourtier.infrastructure.auth.solana_wallet_adapter import (
    SolanaWalletAdapter,
)
from pourtier.infrastructure.blockchain.escrow_contract_client import (
    EscrowContractClient,
)
from pourtier.infrastructure.blockchain.passeur_bridge_client import (
    PasseurBridgeClient,
)
from pourtier.infrastructure.blockchain.passeur_query_service import (
    PasseurQueryService,
)
from pourtier.infrastructure.blockchain.solana_transaction_verifier import (
    SolanaTransactionVerifier,
)
from pourtier.infrastructure.cache.i_cache_client import ICacheClient
from pourtier.infrastructure.cache.multi_layer_cache import MultiLayerCache
from pourtier.infrastructure.cache.redis_cache_client import (
    RedisCacheClient,
)
from pourtier.infrastructure.event_bus.courier_publisher import (
    CourierPublisher,
)
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.repositories.escrow_transaction_repository import (  # noqa: E501
    EscrowTransactionRepository,
)
from pourtier.infrastructure.persistence.repositories.legal_document_repository import (  # noqa: E501
    LegalDocumentRepository,
)
from pourtier.infrastructure.persistence.repositories.subscription_repository import (  # noqa: E501
    SubscriptionRepository,
)
from pourtier.infrastructure.persistence.repositories.user_legal_acceptance_repository import (  # noqa: E501
    UserLegalAcceptanceRepository,
)
from pourtier.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from shared.courier_client import CourierClient


class DIContainer:
    """
    Dependency Injection Container.

    Manages singleton instances of all services and repositories.
    Uses factory pattern for session-scoped dependencies.
    """

    def __init__(self):
        """Initialize container with None instances."""
        # Infrastructure
        self._database: Optional[Database] = None
        self._courier_client: Optional[CourierClient] = None
        self._cache_client: Optional[ICacheClient] = None
        self._multi_layer_cache: Optional[MultiLayerCache] = None

        # Domain Services - Blockchain
        self._passeur_bridge: Optional[IPasseurBridge] = None
        self._blockchain_verifier: Optional[IBlockchainVerifier] = None
        self._escrow_query_service: Optional[IEscrowQueryService] = None

        # Domain Services - Auth
        self._wallet_authenticator: Optional[IWalletAuthenticator] = None

        # Domain Services - Legacy (for tests)
        self._escrow_contract_client: Optional[IEscrowContractClient] = None
        self._event_publisher: Optional[IEventPublisher] = None

        # Repositories (session-scoped, not cached)
        self._user_repository: Optional[IUserRepository] = None
        self._subscription_repository: Optional[ISubscriptionRepository] = None
        self._legal_document_repository: Optional[ILegalDocumentRepository] = None
        self._user_legal_acceptance_repository: Optional[
            IUserLegalAcceptanceRepository
        ] = None
        self._escrow_transaction_repository: Optional[IEscrowTransactionRepository] = (
            None
        )

        # Use Cases (session-scoped, not cached)
        self._authenticate_wallet: Optional[AuthenticateWallet] = None
        self._create_user: Optional[CreateUser] = None
        self._get_user_profile: Optional[GetUserProfile] = None
        self._update_user_profile: Optional[UpdateUserProfile] = None
        self._create_subscription: Optional[CreateSubscription] = None
        self._check_subscription_status: Optional[CheckSubscriptionStatus] = None

    async def initialize(self) -> None:
        """Initialize all services and establish connections."""
        # Initialize database
        await self.database.connect()

        # Initialize Redis cache (if enabled)
        if get_settings().REDIS_ENABLED:
            await self.cache_client.connect()

        # Initialize Courier client
        # (CourierClient handles its own connection)

    async def shutdown(self) -> None:
        """Cleanup resources and close connections."""
        if self._database:
            await self._database.disconnect()

        if self._cache_client:
            await self._cache_client.disconnect()

        if self._escrow_contract_client:
            await self._escrow_contract_client.close()

        if self._passeur_bridge:
            await self._passeur_bridge.close()

        if self._blockchain_verifier:
            await self._blockchain_verifier.close()

        if self._escrow_query_service:
            await self._escrow_query_service.close()

    # Infrastructure Getters

    @property
    def database(self) -> Database:
        """Get database instance."""
        if self._database is None:
            self._database = Database(
                database_url=get_settings().DATABASE_URL,
                echo=get_settings().DATABASE_ECHO,
            )
        return self._database

    @property
    def courier_client(self) -> CourierClient:
        """Get Courier client instance."""
        if self._courier_client is None:
            self._courier_client = CourierClient(base_url=get_settings().COURIER_URL)
        return self._courier_client

    @property
    def cache_client(self) -> ICacheClient:
        """Get Redis cache client instance."""
        if self._cache_client is None:
            self._cache_client = RedisCacheClient(
                host=get_settings().REDIS_HOST,
                port=get_settings().REDIS_PORT,
                db=get_settings().REDIS_DB,
                password=(
                    get_settings().REDIS_PASSWORD
                    if get_settings().REDIS_PASSWORD
                    else None
                ),
            )
        return self._cache_client

    @property
    def multi_layer_cache(self) -> MultiLayerCache:
        """Get multi-layer cache instance (L1 + L2)."""
        if self._multi_layer_cache is None:
            self._multi_layer_cache = MultiLayerCache(
                redis_client=self.cache_client,
                l1_maxsize=1000,
                l1_ttl=300,
                l2_ttl=3600,
            )
        return self._multi_layer_cache

    # Domain Service Getters - Blockchain Services

    @property
    def passeur_bridge(self) -> IPasseurBridge:
        """Get Passeur Bridge client instance."""
        if self._passeur_bridge is None:
            self._passeur_bridge = PasseurBridgeClient(
                bridge_url=get_settings().PASSEUR_URL,
                total_timeout=30,
                connect_timeout=10,
                max_retries=3,
            )
        return self._passeur_bridge

    @property
    def blockchain_verifier(self) -> IBlockchainVerifier:
        """Get blockchain transaction verifier instance."""
        if self._blockchain_verifier is None:
            self._blockchain_verifier = SolanaTransactionVerifier(
                rpc_url=get_settings().SOLANA_RPC_URL,
                total_timeout=30,
            )
        return self._blockchain_verifier

    @property
    def escrow_query_service(self) -> IEscrowQueryService:
        """Get escrow query service instance."""
        if self._escrow_query_service is None:
            self._escrow_query_service = PasseurQueryService(
                bridge_url=get_settings().PASSEUR_URL,
                timeout=30,
            )
        return self._escrow_query_service

    def get_solana_service(self) -> IEscrowQueryService:
        """
        Get Solana service instance (alias for escrow_query_service).

        Returns:
            IEscrowQueryService instance for querying blockchain state
        """
        return self.escrow_query_service

    # Domain Service Getters - Auth

    @property
    def wallet_authenticator(self) -> IWalletAuthenticator:
        """Get wallet authenticator instance (property version)."""
        if self._wallet_authenticator is None:
            self._wallet_authenticator = SolanaWalletAdapter()
        return self._wallet_authenticator

    def get_wallet_authenticator(self) -> IWalletAuthenticator:
        """Get wallet authenticator instance (method version)."""
        return self.wallet_authenticator

    # Domain Service Getters - Legacy (for tests)

    @property
    def escrow_contract_client(self) -> IEscrowContractClient:
        """
        Get smart contract client instance (LEGACY - for tests only).

        NOTE: This is the old client that signs transactions.
        Production code should use passeur_bridge instead.
        """
        if self._escrow_contract_client is None:
            self._escrow_contract_client = EscrowContractClient(
                bridge_url=get_settings().PASSEUR_URL,
                timeout=30,
            )
        return self._escrow_contract_client

    @property
    def event_publisher(self) -> IEventPublisher:
        """Get event publisher instance."""
        if self._event_publisher is None:
            self._event_publisher = CourierPublisher(courier_client=self.courier_client)
        return self._event_publisher

    # Repository Getters (Session-scoped)

    def get_user_repository(self, session: AsyncSession = None) -> IUserRepository:
        """
        Get user repository instance with multi-layer caching.

        Args:
            session: Optional database session. If provided, creates
                    repository with session and cache. If None, returns class
                    (for backwards compatibility).

        Returns:
            UserRepository instance or class
        """
        if session is not None:
            cache = self.multi_layer_cache if get_settings().REDIS_ENABLED else None
            return UserRepository(session, cache=cache)
        return UserRepository

    def get_subscription_repository(
        self, session: AsyncSession = None
    ) -> ISubscriptionRepository:
        """
        Get subscription repository instance.

        Args:
            session: Optional database session. If provided, creates
                    repository with session. If None, returns class
                    (for backwards compatibility).

        Returns:
            SubscriptionRepository instance or class
        """
        if session is not None:
            return SubscriptionRepository(session)
        return SubscriptionRepository

    def get_legal_document_repository(
        self, session: AsyncSession = None
    ) -> ILegalDocumentRepository:
        """
        Get legal document repository instance.

        Args:
            session: Optional database session. If provided, creates
                    repository with session. If None, returns class
                    (for backwards compatibility).

        Returns:
            LegalDocumentRepository instance or class
        """
        if session is not None:
            return LegalDocumentRepository(session)
        return LegalDocumentRepository

    def get_user_legal_acceptance_repository(
        self, session: AsyncSession = None
    ) -> IUserLegalAcceptanceRepository:
        """
        Get user legal acceptance repository instance.

        Args:
            session: Optional database session. If provided, creates
                    repository with session. If None, returns class
                    (for backwards compatibility).

        Returns:
            UserLegalAcceptanceRepository instance or class
        """
        if session is not None:
            return UserLegalAcceptanceRepository(session)
        return UserLegalAcceptanceRepository

    def get_escrow_transaction_repository(
        self, session: AsyncSession = None
    ) -> IEscrowTransactionRepository:
        """
        Get escrow transaction repository instance.

        Args:
            session: Optional database session. If provided, creates
                    repository with session. If None, returns class
                    (for backwards compatibility).

        Returns:
            EscrowTransactionRepository instance or class
        """
        if session is not None:
            return EscrowTransactionRepository(session)
        return EscrowTransactionRepository

    # Use Case Getters

    async def get_authenticate_wallet(
        self, session: AsyncSession
    ) -> AuthenticateWallet:
        """
        Get authenticate wallet use case with session-scoped repository.

        Args:
            session: Active database session

        Returns:
            AuthenticateWallet use case instance
        """
        cache = self.multi_layer_cache if get_settings().REDIS_ENABLED else None
        user_repository = UserRepository(session, cache=cache)

        return AuthenticateWallet(
            user_repository=user_repository,
            wallet_authenticator=self.wallet_authenticator,
        )

    def get_create_user(self) -> CreateUser:
        """Get create user use case."""

    def get_get_user_profile(self) -> GetUserProfile:
        """Get user profile use case."""

    def get_update_user_profile(self) -> UpdateUserProfile:
        """Get update user profile use case."""

    def get_create_subscription(self, session: AsyncSession) -> CreateSubscription:
        """
        Get create subscription use case with session-scoped repos.

        Args:
            session: Active database session

        Returns:
            CreateSubscription use case instance
        """
        subscription_repo = SubscriptionRepository(session)
        cache = self.multi_layer_cache if get_settings().REDIS_ENABLED else None
        user_repo = UserRepository(session, cache=cache)

        return CreateSubscription(
            subscription_repository=subscription_repo,
            user_repository=user_repo,
        )

    def get_check_subscription_status(self) -> CheckSubscriptionStatus:
        """Get check subscription status use case."""


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get global DI container instance."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


async def initialize_container() -> DIContainer:
    """Initialize and return DI container."""
    container = get_container()
    await container.initialize()
    return container


async def shutdown_container() -> None:
    """Shutdown DI container."""
    container = get_container()
    await container.shutdown()
