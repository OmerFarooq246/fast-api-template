from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.users import UserRole


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=1024)]

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).casefold()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).casefold() if value is not None else None


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: Annotated[str, Field(min_length=1, max_length=1024)]
    new_password: Annotated[str, Field(min_length=8, max_length=1024)]


class UserPage(BaseModel):
    items: list[UserResponse]
    page: int
    size: int
    total: int
    pages: int


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=1024)]

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).casefold()


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class LoginSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token scheme, not a credential.
    user: UserResponse | None = None
