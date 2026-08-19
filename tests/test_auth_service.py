from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, Settings
from app.core.security import create_refresh_token, decode_refresh_token
from app.models.refresh_sessions import RefreshSession
from app.models.users import User
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.services.auth_service import AuthService, RefreshReuseDetected, digest_jti
from app.services.user_service import UserService


def build_settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_uri="postgresql+asyncpg://postgres:postgres@localhost/test_unused",
        secret_key="test-secret-that-is-at-least-32-bytes",  # noqa: S106
        jwt_issuer="test-issuer",
        jwt_audience="test-audience",
    )


async def test_login_stores_only_the_refresh_jti_digest() -> None:
    settings = build_settings()
    user = User(email="user@example.com", password="encoded-password")  # noqa: S106
    user.id = 42
    users_mock = create_autospec(UserService, instance=True)
    users_mock.authenticate = AsyncMock(return_value=user)
    sessions_mock = create_autospec(RefreshSessionRepository, instance=True)
    sessions_mock.create = AsyncMock()
    service = AuthService(
        cast(UserService, users_mock),
        cast(RefreshSessionRepository, sessions_mock),
    )

    tokens = await service.login(
        AsyncMock(spec=AsyncSession),
        email=user.email,
        password="password",  # noqa: S106
        settings=settings,
    )

    claims = decode_refresh_token(tokens.refresh_token, settings)
    stored_digest = sessions_mock.create.await_args.kwargs["jti_digest"]
    assert stored_digest == digest_jti(claims.jti)
    assert claims.jti not in stored_digest


async def test_reusing_rotated_token_revokes_its_family() -> None:
    settings = build_settings()
    family_id = uuid4()
    token = create_refresh_token(42, settings=settings)
    stored_session = RefreshSession(
        user_id=42,
        jti_digest=digest_jti(decode_refresh_token(token, settings).jti),
        family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked_at=datetime.now(UTC),
    )
    users_mock = create_autospec(UserService, instance=True)
    sessions_mock = create_autospec(RefreshSessionRepository, instance=True)
    sessions_mock.get_for_update = AsyncMock(return_value=stored_session)
    sessions_mock.revoke_family = AsyncMock()
    service = AuthService(
        cast(UserService, users_mock),
        cast(RefreshSessionRepository, sessions_mock),
    )

    result = await service.rotate(
        AsyncMock(spec=AsyncSession),
        refresh_token=token,
        settings=settings,
    )

    assert isinstance(result, RefreshReuseDetected)
    sessions_mock.revoke_family.assert_awaited_once_with(
        sessions_mock.get_for_update.await_args.args[0], family_id
    )
