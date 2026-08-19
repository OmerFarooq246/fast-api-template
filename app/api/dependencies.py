from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.users import User, UserRole
from app.services.user_service import user_service


def get_app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]

# Function scope guarantees transaction finalization happens before the response is sent.
SessionDep = Annotated[AsyncSession, Depends(get_db, scope="function")]

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: SessionDep,
    settings: SettingsDep,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise AuthenticationError("Authentication credentials were not provided")
    try:
        claims = decode_access_token(credentials.credentials, settings)
        user_id = int(claims.sub)
    except (InvalidTokenError, ValueError) as exc:
        raise AuthenticationError("Could not validate credentials") from exc
    return await user_service.get_authenticated_user(db, user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def ensure_super_admin(current_user: CurrentUserDep) -> User:
    if current_user.role is not UserRole.SUPER_ADMIN:
        raise AuthorizationError("Insufficient privileges")
    return current_user


SuperAdminDep = Annotated[User, Depends(ensure_super_admin)]


async def ensure_admin(current_user: CurrentUserDep) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise AuthorizationError("Insufficient privileges")
    return current_user


AdminDep = Annotated[User, Depends(ensure_admin)]
