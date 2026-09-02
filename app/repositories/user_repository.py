from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.repositories.base import Repository
from app.schemas.users import UserAdminUpdate, UserCreate


class UserRepository(Repository[User, UserCreate, UserAdminUpdate]):
    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


user_repository = UserRepository(User)
