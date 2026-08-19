from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, Settings
from app.core.security import decode_refresh_token, hash_password
from app.models.users import User
from app.services.auth_service import RefreshReuseDetected, TokenPairData, auth_service, digest_jti


@pytest.mark.integration
async def test_refresh_rotation_detects_reuse_and_revokes_the_family(
    db_session: AsyncSession,
) -> None:
    settings = Settings(
        environment=Environment.TEST,
        database_uri="postgresql+asyncpg://postgres:postgres@localhost/test_unused",
        secret_key="test-secret-that-is-at-least-32-bytes",  # noqa: S106
        jwt_issuer="test-issuer",
        jwt_audience="test-audience",
    )
    password = "correct horse battery staple"  # noqa: S105
    user = User(
        email=f"refresh-{uuid4()}@example.com",
        password=hash_password(password),
    )
    db_session.add(user)
    await db_session.flush()

    first_pair = await auth_service.login(
        db_session,
        email=user.email,
        password=password,
        settings=settings,
    )
    second_pair = await auth_service.rotate(
        db_session,
        refresh_token=first_pair.refresh_token,
        settings=settings,
    )
    assert isinstance(second_pair, TokenPairData)

    reuse_result = await auth_service.rotate(
        db_session,
        refresh_token=first_pair.refresh_token,
        settings=settings,
    )

    assert isinstance(reuse_result, RefreshReuseDetected)
    second_claims = decode_refresh_token(second_pair.refresh_token, settings)
    second_session = await auth_service.refresh_sessions.get_for_update(
        db_session, digest_jti(second_claims.jti)
    )
    assert second_session is not None
    assert second_session.revoked_at is not None
