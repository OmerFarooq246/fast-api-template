from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    settings: Settings | None = None,
) -> str:
    application_settings = settings or get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=application_settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        application_settings.secret_key.get_secret_value(),
        algorithm=application_settings.algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    settings: Settings | None = None,
) -> str:
    application_settings = settings or get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=application_settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        application_settings.secret_key.get_secret_value(),
        algorithm=application_settings.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    application_settings = settings or get_settings()
    return jwt.decode(
        token,
        application_settings.secret_key.get_secret_value(),
        algorithms=[application_settings.algorithm],
    )


bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    token = credentials.credentials
    settings = cast(Settings, request.app.state.settings)
    try:
        payload = decode_access_token(token, settings)
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    print(f"payload: {payload}")
    return payload


async def ensuer_super_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    role = current_user.get("role")
    print(f"role: {role}")
    if role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Access denied: Insufficient privileges.")
    return current_user


async def ensuer_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    role = current_user.get("role")
    print(f"role: {role}")
    if role != "ADMIN" and role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Access denied: Insufficient privileges.")
    return current_user
