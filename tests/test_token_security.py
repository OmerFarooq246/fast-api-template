from datetime import timedelta

import pytest
from jwt import InvalidTokenError

from app.core.config import Environment, Settings
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


@pytest.fixture
def token_settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_uri="postgresql+asyncpg://postgres:postgres@localhost/test_unused",
        secret_key="test-secret-that-is-at-least-32-bytes",  # noqa: S106
        jwt_issuer="test-issuer",
        jwt_audience="test-audience",
    )


def test_access_token_has_required_validated_claims(token_settings: Settings) -> None:
    token = create_access_token(42, settings=token_settings)

    claims = decode_access_token(token, token_settings)

    assert claims.sub == "42"
    assert claims.iss == "test-issuer"
    assert claims.aud == "test-audience"
    assert claims.jti
    assert claims.token_type is TokenType.ACCESS
    assert claims.exp > claims.iat


def test_token_types_are_not_interchangeable(token_settings: Settings) -> None:
    refresh_token = create_refresh_token(42, settings=token_settings)

    with pytest.raises(InvalidTokenError, match="Expected token type: access"):
        decode_access_token(refresh_token, token_settings)


def test_refresh_token_uses_its_own_lifetime(token_settings: Settings) -> None:
    refresh_token = create_refresh_token(42, settings=token_settings)

    claims = decode_refresh_token(refresh_token, token_settings)

    assert claims.token_type is TokenType.REFRESH
    assert claims.exp - claims.iat == timedelta(days=token_settings.refresh_token_expire_days)


def test_expired_tokens_are_rejected(token_settings: Settings) -> None:
    token = create_access_token(42, settings=token_settings, expires_delta=timedelta(seconds=-1))

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, token_settings)


def test_wrong_audience_is_rejected(token_settings: Settings) -> None:
    token = create_access_token(42, settings=token_settings)
    other_audience = token_settings.model_copy(update={"jwt_audience": "another-api"})

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, other_audience)
