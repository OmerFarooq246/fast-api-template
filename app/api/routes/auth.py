from fastapi import APIRouter
from jwt import InvalidTokenError

from app.api.dependencies import SessionDep, SettingsDep
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.schemas.users import LoginSchema, RefreshTokenRequest, UserLoginSchema
from app.services.user_service import user_service

router = APIRouter()


@router.post("/login", response_model=LoginSchema, summary="Login existing user")
async def login(
    login_data: UserLoginSchema,
    db: SessionDep,
    settings: SettingsDep,
) -> LoginSchema:
    user = await user_service.authenticate(db, str(login_data.email), login_data.password)
    return LoginSchema(
        access_token=create_access_token(user.id, settings=settings),
        refresh_token=create_refresh_token(user.id, settings=settings),
        user=user,
    )


@router.post("/refresh", response_model=LoginSchema, summary="Refresh authentication tokens")
async def refresh_token(
    request: RefreshTokenRequest,
    db: SessionDep,
    settings: SettingsDep,
) -> LoginSchema:
    try:
        claims = decode_refresh_token(request.refresh_token, settings)
        user_id = int(claims.sub)
    except (InvalidTokenError, ValueError) as exc:
        raise AuthenticationError("Invalid or expired refresh token") from exc

    user = await user_service.get_authenticated_user(db, user_id)
    return LoginSchema(
        access_token=create_access_token(user.id, settings=settings),
        refresh_token=create_refresh_token(user.id, settings=settings),
        user=user,
    )
