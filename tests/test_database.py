from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


async def test_application_owns_typed_async_database_resources(app: FastAPI) -> None:
    assert isinstance(app.state.db_engine, AsyncEngine)
    assert isinstance(app.state.db_session_factory, async_sessionmaker)

    session = app.state.db_session_factory()
    assert isinstance(session, AsyncSession)
    await session.close()
