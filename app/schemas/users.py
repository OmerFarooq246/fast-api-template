from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CreateUserSchema(BaseModel):
    email: Annotated[str, Field(..., min_length=3, max_length=50)]
    password: Annotated[str, Field(..., min_length=8)]
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UpdateUserSchema(BaseModel):
    email: Annotated[str | None, Field(min_length=3, max_length=50)] = None
    password: Annotated[str | None, Field(min_length=8)] = None
    role: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserLoginSchema(BaseModel):
    email: str
    password: str


class LoginSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token scheme, not a credential.
    user: UserResponseSchema | None = None
