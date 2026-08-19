from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import Settings, get_settings

password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    iss: str
    aud: str
    iat: datetime
    exp: datetime
    jti: str
    token_type: TokenType


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    valid, _ = verify_and_update_password(plain_password, hashed_password)
    return valid


def verify_and_update_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    try:
        return password_hash.verify_and_update(plain_password, hashed_password)
    except UnknownHashError:
        return False, None


def create_token(
    subject: int,
    token_type: TokenType,
    *,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
    jti: str | None = None,
) -> str:
    application_settings = settings or get_settings()
    now = datetime.now(UTC)
    default_lifetime = (
        timedelta(minutes=application_settings.access_token_expire_minutes)
        if token_type is TokenType.ACCESS
        else timedelta(days=application_settings.refresh_token_expire_days)
    )
    payload = {
        "sub": str(subject),
        "iss": application_settings.jwt_issuer,
        "aud": application_settings.jwt_audience,
        "iat": now,
        "exp": now + (expires_delta or default_lifetime),
        "jti": jti or str(uuid4()),
        "token_type": token_type.value,
    }
    return jwt.encode(
        payload,
        application_settings.secret_key.get_secret_value(),
        algorithm=application_settings.algorithm,
    )


def create_access_token(
    subject: int,
    *,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    return create_token(
        subject,
        TokenType.ACCESS,
        settings=settings,
        expires_delta=expires_delta,
    )


def create_refresh_token(
    subject: int,
    *,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
    jti: str | None = None,
) -> str:
    return create_token(
        subject,
        TokenType.REFRESH,
        settings=settings,
        expires_delta=expires_delta,
        jti=jti,
    )


def decode_token(
    token: str,
    expected_type: TokenType,
    *,
    settings: Settings | None = None,
) -> TokenClaims:
    application_settings = settings or get_settings()
    payload = jwt.decode(
        token,
        application_settings.secret_key.get_secret_value(),
        algorithms=[application_settings.algorithm],
        audience=application_settings.jwt_audience,
        issuer=application_settings.jwt_issuer,
        options={
            "require": ["sub", "iss", "aud", "iat", "exp", "jti", "token_type"],
            "strict_aud": True,
        },
    )
    try:
        claims = TokenClaims.model_validate(payload)
    except ValidationError as exc:
        raise InvalidTokenError("Invalid token claims") from exc
    if claims.token_type is not expected_type:
        raise InvalidTokenError(f"Expected token type: {expected_type.value}")
    return claims


def decode_access_token(token: str, settings: Settings | None = None) -> TokenClaims:
    return decode_token(token, TokenType.ACCESS, settings=settings)


def decode_refresh_token(token: str, settings: Settings | None = None) -> TokenClaims:
    return decode_token(token, TokenType.REFRESH, settings=settings)
