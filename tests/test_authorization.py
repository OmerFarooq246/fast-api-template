from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import ensure_admin, ensure_super_admin
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def build_user(role: UserRole = UserRole.USER, *, is_active: bool = True) -> User:
    user = User(
        email=f"{role.value.casefold()}@example.com",
        password="encoded-password",  # noqa: S106
        role=role,
        is_active=is_active,
    )
    user.id = 42
    return user


async def test_admin_dependency_accepts_admin_and_super_admin() -> None:
    admin = build_user(UserRole.ADMIN)
    super_admin = build_user(UserRole.SUPER_ADMIN)

    assert await ensure_admin(admin) is admin
    assert await ensure_admin(super_admin) is super_admin


async def test_admin_dependency_rejects_regular_user() -> None:
    with pytest.raises(AuthorizationError, match="Insufficient privileges"):
        await ensure_admin(build_user())


async def test_super_admin_dependency_rejects_admin() -> None:
    with pytest.raises(AuthorizationError, match="Insufficient privileges"):
        await ensure_super_admin(build_user(UserRole.ADMIN))


async def test_super_admin_dependency_accepts_super_admin() -> None:
    super_admin = build_user(UserRole.SUPER_ADMIN)

    assert await ensure_super_admin(super_admin) is super_admin


@pytest.mark.parametrize("stored_user", [None, build_user(is_active=False)])
async def test_authentication_rejects_deleted_or_inactive_account(
    stored_user: User | None,
) -> None:
    repository_mock = create_autospec(UserRepository, instance=True)
    repository_mock.get = AsyncMock(return_value=stored_user)
    service = UserService(cast(UserRepository, repository_mock))

    with pytest.raises(AuthenticationError, match="Could not validate credentials"):
        await service.get_authenticated_user(AsyncMock(), 42)


def test_protected_route_rejects_missing_credentials(client: TestClient) -> None:
    response = client.get("/users/")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "authentication_failed"
