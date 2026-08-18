from math import ceil

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from app.api.dependencies import SessionDep
from app.core.security import ensuer_super_admin
from app.models.users import User
from app.schemas.users import UserAdminUpdate, UserCreate, UserPage, UserResponse
from app.services.user_service import user_service

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def create_user(
    user_in: UserCreate,
    db: SessionDep,
) -> User:
    user = await user_service.create(db, user_in)
    return user


@router.get("/{user_id}", response_model=UserResponse, summary="Get a user by id")
async def get_user(
    user_id: int,
    db: SessionDep,
    current_user: User = Depends(ensuer_super_admin),
) -> User:
    user = await user_service.get(db, user_id)
    return user


@router.get("/", response_model=UserPage, summary="List users")
async def get_all_users(
    db: SessionDep,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(ensuer_super_admin),
) -> UserPage:
    users, total = await user_service.list_page(db, page=page, size=size)
    return UserPage(
        items=[UserResponse.model_validate(user) for user in users],
        page=page,
        size=size,
        total=total,
        pages=ceil(total / size),
    )


@router.patch("/{user_id}", response_model=UserResponse, summary="Administratively update a user")
async def update_user(
    user_id: int,
    user_in: UserAdminUpdate,
    db: SessionDep,
    current_user: User = Depends(ensuer_super_admin),
) -> User:
    updated_user = await user_service.update(db, user_id, user_in)
    return updated_user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user against an id"
)
async def delete_user(
    user_id: int,
    db: SessionDep,
    current_user: User = Depends(ensuer_super_admin),
) -> Response:
    await user_service.delete(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
