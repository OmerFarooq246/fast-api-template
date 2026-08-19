import asyncio
from typing import Literal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.exceptions import ResourceConflictError
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.schemas.users import UserCreate
from app.services.user_service import UserService


class CoordinatedUserRepository(UserRepository):
    def __init__(self, barrier: asyncio.Barrier) -> None:
        super().__init__(User)
        self.barrier = barrier

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        user = await super().get_by_email(session, email)
        await self.barrier.wait()
        return user


@pytest.mark.integration
async def test_database_constraint_resolves_concurrent_email_creation(
    test_engine: AsyncEngine,
) -> None:
    email = f"race-{uuid4()}@example.com"
    service = UserService(CoordinatedUserRepository(asyncio.Barrier(2)))
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def create_user() -> Literal["created", "conflict"]:
        try:
            async with session_factory() as session, session.begin():
                await service.create(
                    session,
                    UserCreate(email=email, password="strong-password"),  # noqa: S106
                )
        except ResourceConflictError:
            return "conflict"
        return "created"

    async with asyncio.timeout(10):
        results = await asyncio.gather(create_user(), create_user())

    assert sorted(results) == ["conflict", "created"]
    async with session_factory() as session:
        count = await session.scalar(
            select(func.count()).select_from(User).where(User.email == email)
        )
    assert count == 1
