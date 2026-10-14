from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.repositories.user_repository import UserRepository


@pytest.mark.integration
async def test_cursor_traversal_survives_deletion_and_insertion(db_session: AsyncSession) -> None:
    repository = UserRepository(User)
    initial_cursor = await db_session.scalar(select(func.max(User.id)))
    users = [
        User(email=f"pagination-{uuid4()}@example.com", password="hashed-password")  # noqa: S106
        for _ in range(5)
    ]
    db_session.add_all(users)
    await db_session.flush()
    expected_ids = [user.id for user in users]

    first, cursor = await repository.list_page(db_session, cursor=initial_cursor, limit=2)
    assert [user.id for user in first] == expected_ids[:2]
    assert cursor == expected_ids[1]

    await repository.delete(db_session, first[0])
    await repository.delete(db_session, first[1])
    inserted = User(email=f"pagination-{uuid4()}@example.com", password="hashed-password")  # noqa: S106
    db_session.add(inserted)
    await db_session.flush()

    second, cursor = await repository.list_page(db_session, cursor=cursor, limit=2)
    assert [user.id for user in second] == expected_ids[2:4]
    assert cursor == expected_ids[3]
    third, cursor = await repository.list_page(db_session, cursor=cursor, limit=2)
    assert [user.id for user in third] == [expected_ids[4], inserted.id]
    assert cursor is None
    assert await repository.list_page(db_session, cursor=inserted.id, limit=2) == ([], None)
