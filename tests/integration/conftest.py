from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine


class IntegrationTestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_database_uri: str | None = None


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator[AsyncEngine]:
    database_uri = IntegrationTestSettings().test_database_uri
    if database_uri is None:
        pytest.skip("TEST_DATABASE_URI is not configured")

    database_name = make_url(database_uri).database
    if database_name is None or "test" not in database_name.lower():
        raise RuntimeError(
            "TEST_DATABASE_URI must point to a database containing 'test' in its name"
        )

    engine = create_async_engine(database_uri, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
