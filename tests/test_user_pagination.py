from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ensure_super_admin
from app.db.database import get_db
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService, user_service


@pytest.fixture
def pagination_client(app: FastAPI, client: TestClient) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: AsyncMock(spec=AsyncSession)
    app.dependency_overrides[ensure_super_admin] = lambda: User(role=UserRole.SUPER_ADMIN)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("cursor", [None, 42])
async def test_service_passes_cursor_to_repository(cursor: int | None) -> None:
    repository = create_autospec(UserRepository, instance=True)
    repository.list_page.return_value = ([], None)
    session = AsyncMock(spec=AsyncSession)

    result = await UserService(cast(UserRepository, repository)).list_page(
        session, cursor=cursor, size=20
    )

    assert result == ([], None)
    repository.list_page.assert_awaited_once_with(session, cursor=cursor, limit=20)


@pytest.mark.parametrize("next_cursor", [42, None])
def test_users_cursor_response(
    pagination_client: TestClient, monkeypatch: pytest.MonkeyPatch, next_cursor: int | None
) -> None:
    user = User(
        id=42,
        email="user@example.com",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    list_page = AsyncMock(return_value=([user], next_cursor))
    monkeypatch.setattr(user_service, "list_page", list_page)

    response = pagination_client.get("/users/?cursor=40&size=1")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "size", "next_cursor"}
    assert body["items"][0]["id"] == 42
    assert body["next_cursor"] == next_cursor
    assert body["size"] == 1
    assert list_page.call_args.kwargs == {"cursor": 40, "size": 1}


def test_users_first_page_defaults(
    pagination_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    list_page = AsyncMock(return_value=([], None))
    monkeypatch.setattr(user_service, "list_page", list_page)

    response = pagination_client.get("/users/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "size": 20, "next_cursor": None}
    assert list_page.call_args.kwargs == {"cursor": None, "size": 20}


@pytest.mark.parametrize(
    "query",
    ["cursor=0", "cursor=-1", "cursor=abc", "cursor=2147483648", "size=0", "size=101"],
)
def test_users_rejects_invalid_pagination(
    pagination_client: TestClient, monkeypatch: pytest.MonkeyPatch, query: str
) -> None:
    list_page = AsyncMock()
    monkeypatch.setattr(user_service, "list_page", list_page)

    assert pagination_client.get(f"/users/?{query}").status_code == 422
    list_page.assert_not_awaited()
