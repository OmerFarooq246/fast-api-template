from fastapi import APIRouter, HTTPException
from jose import ExpiredSignatureError, JWTError

from app.api.dependencies import SessionDep, SettingsDep
from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.schemas.users import LoginSchema, UserLoginSchema
from app.services.user_service import user_service

router = APIRouter()


@router.post("/login", response_model=LoginSchema, summary="Login existing user")
async def login(
    login_data: UserLoginSchema,
    db: SessionDep,
    settings: SettingsDep,
) -> LoginSchema:
    user = await user_service.authenticate(db, login_data.email, login_data.password)
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = create_access_token(token_data, settings=settings)
    refresh_token = create_refresh_token(token_data, settings=settings)
    return LoginSchema(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/referesh", response_model=LoginSchema, summary="Refresh access token")
async def refresh_token(refresh_token: str, settings: SettingsDep) -> LoginSchema:
    try:
        payload = decode_access_token(refresh_token, settings)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        token_data = {"sub": payload["sub"], "email": payload["email"], "role": payload["role"]}
        access_token = create_access_token(token_data, settings=settings)
        new_refresh_token = create_refresh_token(token_data, settings=settings)
        return LoginSchema(access_token=access_token, refresh_token=new_refresh_token)
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Refresh token expired") from exc
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
