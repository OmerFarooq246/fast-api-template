from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exception_handlers import CRUDException
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
                print(f"duplicate email in {self.model.__name__} create: {e}")
                raise CRUDException(self.model.__name__, "duplicate email in create") from e
            print(f"error in {self.model.__name__} create: {e}")
            raise CRUDException(self.model.__name__, f"error in create: {e}") from e

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Users:
        users = await self.get_by_attribute(db, "email", email)
        user = users[0]
        if not user or not verify_password(password, user.password):
            print(f"error in {self.model.__name__} authenticate: incorrect password")
            raise CRUDException(
                self.model.__name__, "error in authenticate: incorrect password", 401
            )
        return user


user_crud = UserCRUD(Users)
