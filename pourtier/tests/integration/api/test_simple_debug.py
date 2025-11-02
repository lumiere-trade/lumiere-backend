"""Simple debug test to see actual response"""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4
import httpx

from pourtier.config.settings import get_settings
from pourtier.di.dependencies import get_db_session, get_escrow_query_service
from pourtier.domain.entities.user import User
from pourtier.infrastructure.persistence.database import Database
from pourtier.infrastructure.persistence.models import Base
from pourtier.infrastructure.persistence.repositories.user_repository import UserRepository
from pourtier.main import create_app
from shared.tests import LaborantTest


class TestSimpleDebug(LaborantTest):
    component_name = "pourtier"
    test_category = "integration"
    
    async def async_setup(self):
        settings = get_settings()
        self.db = Database(database_url=settings.DATABASE_URL, echo=False)
        await self.db.connect()
        await self.db.reset_schema_for_testing(Base.metadata)

        self.mock_escrow_query = AsyncMock()
        self.mock_escrow_query.check_escrow_exists.return_value = True

        app = create_app(settings)

        async def override_get_db_session():
            async with self.db.session() as session:
                yield session

        def override_get_escrow_query():
            return self.mock_escrow_query

        app.dependency_overrides[get_db_session] = override_get_db_session
        app.dependency_overrides[get_escrow_query_service] = override_get_escrow_query

        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

        async with self.db.session() as session:
            user_repo = UserRepository(session)
            unique_wallet = str(uuid4()).replace("-", "").ljust(44, "0")
            user = User(wallet_address=unique_wallet)
            user.update_escrow_balance(Decimal("500.0"))
            self.test_user = await user_repo.create(user)

        from pourtier.infrastructure.auth.jwt_handler import create_access_token
        self.test_token = create_access_token(
            user_id=self.test_user.id,
            wallet_address=self.test_user.wallet_address,
        )

    async def async_teardown(self):
        if self.client:
            await self.client.aclose()
        if self.db:
            await self.db.disconnect()

    async def test_see_actual_response(self):
        """See what API actually returns."""
        self.reporter.info("Making request...", context="Test")
        
        response = await self.client.post(
            "/api/subscriptions/",
            json={"plan_type": "basic"},
            headers={"Authorization": f"Bearer {self.test_token}"},
        )
        
        self.reporter.info(f"Status: {response.status_code}", context="Test")
        self.reporter.info(f"Body: {response.text}", context="Test")
        self.reporter.info(f"Headers: {dict(response.headers)}", context="Test")
        
        # Force it to pass so we see the output
        assert True


if __name__ == "__main__":
    TestSimpleDebug.run_as_main()
