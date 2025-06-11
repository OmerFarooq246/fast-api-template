from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.users import Users
from app.schemas.users import CreateUserSchema, UpdateUserSchema, UserResponseSchema
from app.db.user_crud import user_crud

router = APIRouter()

@router.post("/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED, summary="Register new user")
async def create_user(
    user_in: CreateUserSchema,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.create(db, user_in)
    return user


@router.get("/{user_id}", response_model=UserResponseSchema, summary="Get a new user against an id")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    user = await user_crud.get(db, user_id)
    return user


@router.get("/", response_model=List[UserResponseSchema], summary="Get all users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    users = await user_crud.get_all(db)
    if not users:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return users

#handle pass hash if found => remaining
@router.patch("/{user_id}", response_model=UserResponseSchema, summary="Edit a user against an id")
async def update_user(
    user_id: int, 
    user_in: UpdateUserSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    db_user = await user_crud.get(db, user_id)
    updated_user = await user_crud.update(db, db_user, user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user against an id")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    await user_crud.delete(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
