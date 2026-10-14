from unittest.mock import AsyncMock, Mock

import pytest
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


@pytest.mark.parametrize(
    ("ids", "expected_ids", "next_cursor"),
    [([], [], None), ([2], [2], None), ([2, 5], [2, 5], None), ([2, 5, 9], [2, 5], 5)],
)
async def test_cursor_page_detects_more_results(
    ids: list[int], expected_ids: list[int], next_cursor: int | None
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = Mock(all=Mock(return_value=[User(id=id_) for id_ in ids]))

    items, cursor = await UserRepository(User).list_page(session, limit=2)

    assert [item.id for item in items] == expected_ids
    assert cursor == next_cursor
    statement = session.scalars.call_args.args[0]
    sql = str(statement.compile())
    assert "ORDER BY users.id ASC" in sql
    assert "WHERE" not in sql
    assert "OFFSET" not in sql
    assert statement.compile().params == {"param_1": 3}
    session.scalar.assert_not_awaited()


async def test_cursor_page_seeks_after_the_last_id() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = Mock(all=Mock(return_value=[]))

    assert await UserRepository(User).list_page(session, cursor=42, limit=20) == ([], None)

    statement = session.scalars.call_args.args[0]
    sql = str(statement.compile())
    assert "WHERE users.id >" in sql
    assert "OFFSET" not in sql
    assert statement.compile().params == {"id_1": 42, "param_1": 21}


@pytest.mark.parametrize("limit", [0, -1])
async def test_cursor_page_rejects_nonpositive_limit(limit: int) -> None:
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(ValueError, match="limit must be positive"):
        await UserRepository(User).list_page(session, limit=limit)

    session.scalars.assert_not_awaited()
