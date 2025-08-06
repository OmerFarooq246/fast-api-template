from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, ExpiredSignatureError
from app.db.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.schemas.users import LoginSchema, UserLoginSchema
from app.db.user_crud import user_crud

router = APIRouter()

@router.post("/login", response_model=LoginSchema, summary="Login existing user")
async def login(login_data: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    user = await user_crud.authenticate(db, login_data.email, login_data.password)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return LoginSchema(access_token=access_token, refresh_token=refresh_token, user=user)

@router.post("/referesh", response_model=LoginSchema, summary="Refresh access token")
async def refresh_token(refresh_token: str):
    try:
        payload = decode_access_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "role": payload["role"]
        }
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        return LoginSchema(access_token=access_token, refresh_token=new_refresh_token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")