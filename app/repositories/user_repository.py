from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.repositories.base import Repository
from app.schemas.users import UserAdminUpdate, UserCreate


class UserRepository(Repository[User, UserCreate, UserAdminUpdate]):
    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_page(
        self, session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[User], int]:
        users = await session.scalars(
            select(User).order_by(User.id.asc()).offset(offset).limit(limit)
        )
        total = await session.scalar(select(func.count()).select_from(User))
        return list(users.all()), total or 0


user_repository = UserRepository(User)
