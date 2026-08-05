from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, PersistenceError, ResourceConflictError
from app.core.security import hash_password, verify_password
from app.db.crud_base import CRUDBase
from app.models.users import Users
from app.schemas.users import CreateUserSchema, UpdateUserSchema


class UserCRUD(CRUDBase[Users, CreateUserSchema, UpdateUserSchema]):
    async def create(self, db: AsyncSession, obj_in: CreateUserSchema) -> Users:
        try:
            hashed = hash_password(obj_in.password)
            db_obj = self.model(**obj_in.model_dump())
            db_obj.password = hashed
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            if "ix_users_email" in str(e):
                raise ResourceConflictError("A user with this email already exists") from e
            raise PersistenceError(self.model.__name__, "create") from e

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Users:
        users = await self.get_by_attribute(db, "email", email)
        user = users[0]
        if not user or not verify_password(password, user.password):
            raise AuthenticationError("Incorrect email or password")
        return user


user_crud = UserCRUD(Users)
