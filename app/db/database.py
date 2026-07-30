from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import config

# Configure SQLAlchemy for PostgreSQL
SQLALCHEMY_DATABASE_URL = config.DATABASE_URI

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create async session factory
async_session = sessionmaker(  # type: ignore[call-overload]  # Replaced in Module 2.
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base: Any = declarative_base()


# Dependency for FastAPI
async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
