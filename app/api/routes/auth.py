from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response

from app.api.dependencies import CurrentUserDep, SessionDep, SettingsDep
from app.api.exception_handlers import application_exception_handler
from app.core.exceptions import RefreshTokenReuseError
from app.schemas.users import (
    LoginSchema,
    PasswordChange,
    RefreshTokenRequest,
    UserLoginSchema,
)
from app.services.auth_service import RefreshReuseDetected, TokenPairData, auth_service

router = APIRouter()


def build_login_response(tokens: TokenPairData) -> LoginSchema:
    return LoginSchema(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=tokens.user,
    )


@router.post("/login", response_model=LoginSchema, summary="Login existing user")
async def login(
    login_data: UserLoginSchema,
    db: SessionDep,
    settings: SettingsDep,
) -> LoginSchema:
    tokens = await auth_service.login(
        db,
        email=str(login_data.email),
        password=login_data.password,
        settings=settings,
    )
    return build_login_response(tokens)


@router.post("/refresh", response_model=LoginSchema, summary="Rotate authentication tokens")
async def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: SessionDep,
    settings: SettingsDep,
) -> LoginSchema | JSONResponse:
    result = await auth_service.rotate(
        db,
        refresh_token=request.refresh_token,
        settings=settings,
    )
    if isinstance(result, RefreshReuseDetected):
        # Returning the error response allows the family revocation to commit.
        return await application_exception_handler(
            http_request,
            RefreshTokenReuseError("Refresh token reuse detected"),
        )
    tokens = result
    return build_login_response(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a refresh token")
async def logout(
    request: RefreshTokenRequest,
    db: SessionDep,
    settings: SettingsDep,
) -> Response:
    await auth_service.logout(db, refresh_token=request.refresh_token, settings=settings)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all refresh sessions",
)
async def logout_all(current_user: CurrentUserDep, db: SessionDep) -> Response:
    await auth_service.logout_all(db, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the current user's password",
)
async def change_password(
    request: PasswordChange,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> Response:
    await auth_service.change_password(
        db,
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
