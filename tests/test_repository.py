from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.schemas.users import UserCreate


async def test_repository_flushes_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = UserRepository(User)

    user = await repository.create(
        session,
        UserCreate(
            email="user@example.com",
            password="hashed-password",  # noqa: S106
        ),
    )

    assert user.email == "user@example.com"
    session.flush.assert_awaited_once_with()
    session.refresh.assert_awaited_once_with(user)
    session.commit.assert_not_awaited()
    session.rollback.assert_not_awaited()
