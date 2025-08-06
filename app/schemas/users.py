from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime

class CreateUserSchema(BaseModel):
    email: Annotated[str, Field(..., min_length=3, max_length=50)]
    password: Annotated[str, Field(..., min_length=8)]
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime


class UpdateUserSchema(BaseModel):
    email: Annotated[Optional[str], Field(min_length=3, max_length=50)] = None
    password: Annotated[Optional[str], Field(min_length=8)] = None
    role: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserLoginSchema(BaseModel):
    email: str
    password: str


class LoginSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponseSchema] = None