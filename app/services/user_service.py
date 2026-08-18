from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password, verify_and_update_password
from app.models.users import User
from app.repositories.user_repository import UserRepository, user_repository
from app.schemas.users import UserAdminUpdate, UserCreate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get(self, session: AsyncSession, user_id: int) -> User:
        user = await self.repository.get(session, user_id)
        if user is None:
            raise ResourceNotFoundError("User", user_id)
        return user

    async def list_page(
        self, session: AsyncSession, *, page: int, size: int
    ) -> tuple[list[User], int]:
        return await self.repository.list_page(session, offset=(page - 1) * size, limit=size)

    async def create(self, session: AsyncSession, data: UserCreate) -> User:
        if await self.repository.get_by_email(session, data.email) is not None:
            raise ResourceConflictError("A user with this email already exists")

        create_data = data.model_copy(update={"password": hash_password(data.password)})
        try:
            return await self.repository.create(session, create_data)
        except IntegrityError as exc:
            # The database constraint remains authoritative under concurrent requests.
            raise ResourceConflictError("A user with this email already exists") from exc

    async def update(
        self,
        session: AsyncSession,
        user_id: int,
        data: UserAdminUpdate,
    ) -> User:
        user = await self.get(session, user_id)
        try:
            return await self.repository.update(session, user, data)
        except IntegrityError as exc:
            raise ResourceConflictError("A user with this email already exists") from exc

    async def delete(self, session: AsyncSession, user_id: int) -> None:
        user = await self.get(session, user_id)
        await self.repository.delete(session, user)

    async def authenticate(self, session: AsyncSession, email: str, password: str) -> User:
        user = await self.repository.get_by_email(session, email)
        if user is None:
            raise AuthenticationError("Incorrect email or password")

        valid, updated_hash = verify_and_update_password(password, user.password)
        if not valid:
            raise AuthenticationError("Incorrect email or password")
        if updated_hash is not None:
            user.password = updated_hash
            await session.flush()
        return user

    async def change_password(
        self,
        session: AsyncSession,
        user: User,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        valid, _ = verify_and_update_password(current_password, user.password)
        if not valid:
            raise AuthenticationError("Current password is incorrect")
        user.password = hash_password(new_password)
        await session.flush()


user_service = UserService(user_repository)
