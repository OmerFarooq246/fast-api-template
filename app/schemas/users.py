from pydantic import BaseModel, Field
from typing import Optional


class CreateUserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

    class Config:
        orm_mode = True


class UpdateUserSchema(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)

    class Config:
        orm_mode = True
