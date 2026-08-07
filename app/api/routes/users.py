from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from app.api.dependencies import SessionDep
from app.core.security import ensuer_super_admin
from app.models.users import Users
from app.schemas.users import CreateUserSchema, UpdateUserSchema, UserResponseSchema
from app.services.user_service import user_service

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def create_user(
    user_in: CreateUserSchema,
    db: SessionDep,
) -> Users:
    user = await user_service.create(db, user_in)
    return user


@router.get("/{user_id}", response_model=UserResponseSchema, summary="Get a new user against an id")
async def get_user(
    user_id: int,
    db: SessionDep,
    current_user: Users = Depends(ensuer_super_admin),
) -> Users:
    user = await user_service.get(db, user_id)
    return user


@router.get("/", response_model=list[UserResponseSchema], summary="Get all users")
async def get_all_users(
    db: SessionDep,
    current_user: Users = Depends(ensuer_super_admin),
) -> list[Users] | Response:
    users = await user_service.list(db)
    if not users:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return users


@router.patch("/{user_id}", response_model=UserResponseSchema, summary="Edit a user against an id")
async def update_user(
    user_id: int,
    user_in: UpdateUserSchema,
    db: SessionDep,
    current_user: Users = Depends(ensuer_super_admin),
) -> Users:
    updated_user = await user_service.update(db, user_id, user_in)
    return updated_user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user against an id"
)
async def delete_user(
    user_id: int,
    db: SessionDep,
    current_user: Users = Depends(ensuer_super_admin),
) -> Response:
    await user_service.delete(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
