from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.db.crud_base import CRUDBase
from app.models.users import Users
from app.schemas.users import CreateUserSchema, UpdateUserSchema

router = APIRouter()

# Instantiate the CRUD object for Users
user_crud = CRUDBase[Users, CreateUserSchema, UpdateUserSchema](Users)


@router.post("/", response_model=CreateUserSchema, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user(user_in: CreateUserSchema, db: AsyncSession = Depends(get_db)):
    user = await user_crud.create(db, user_in)
    return user


@router.get("/{user_id}", response_model=CreateUserSchema, summary="Get a new user against an id")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get(db, user_id)
    return user


@router.get("/", response_model=List[CreateUserSchema], summary="Get all users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = await user_crud.get_all(db)
    return users


@router.put("/{user_id}", response_model=CreateUserSchema, summary="Edit a user against an id")
async def update_user(user_id: int, user_in: UpdateUserSchema, db: AsyncSession = Depends(get_db)):
    db_user = await user_crud.get(db, user_id)
    updated_user = await user_crud.update(db, db_user, user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user against an id")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await user_crud.delete(db, user_id)
    return None
