from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import Users
from app.repositories.base import Repository
from app.schemas.users import CreateUserSchema, UpdateUserSchema


class UserRepository(Repository[Users, CreateUserSchema, UpdateUserSchema]):
    async def get_by_email(self, session: AsyncSession, email: str) -> Users | None:
        result = await session.execute(select(Users).where(Users.email == email))
        return result.scalar_one_or_none()


user_repository = UserRepository(Users)
