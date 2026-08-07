from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password, verify_password
from app.models.users import Users
from app.repositories.user_repository import UserRepository, user_repository
from app.schemas.users import CreateUserSchema, UpdateUserSchema


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get(self, session: AsyncSession, user_id: int) -> Users:
        user = await self.repository.get(session, user_id)
        if user is None:
            raise ResourceNotFoundError("User", user_id)
        return user

    async def list(self, session: AsyncSession) -> list[Users]:
        return await self.repository.list(session)

    async def create(self, session: AsyncSession, data: CreateUserSchema) -> Users:
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
        data: UpdateUserSchema,
    ) -> Users:
        user = await self.get(session, user_id)
        if data.password is not None:
            data = data.model_copy(update={"password": hash_password(data.password)})
        try:
            return await self.repository.update(session, user, data)
        except IntegrityError as exc:
            raise ResourceConflictError("A user with this email already exists") from exc

    async def delete(self, session: AsyncSession, user_id: int) -> None:
        user = await self.get(session, user_id)
        await self.repository.delete(session, user)

    async def authenticate(self, session: AsyncSession, email: str, password: str) -> Users:
        user = await self.repository.get_by_email(session, email)
        if user is None or not verify_password(password, user.password):
            raise AuthenticationError("Incorrect email or password")
        return user


user_service = UserService(user_repository)
