from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    id: Mapped[int] = mapped_column(primary_key=True)


def create_db_engine(database_uri: str, *, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_uri, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    session_factory: Any = request.app.state.db_session_factory
    if not isinstance(session_factory, async_sessionmaker):
        raise RuntimeError("Database session factory is not configured")
    return session_factory


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory(request)
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
