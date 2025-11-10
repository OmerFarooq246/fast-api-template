from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import config
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])


bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        id: str = payload.get("sub")
        if id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"payload: {payload}")
    return payload


async def ensuer_super_admin(
    current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    print(f"role: {role}")
    if role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Access denied: Insufficient privileges."
        )
    return current_user


async def ensuer_admin(
    current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    print(f"role: {role}")
    if role != "ADMIN" and role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Access denied: Insufficient privileges."
        )
    return current_user