from app.db.crud_base import CRUDBase
from app.models.users import Users
from app.schemas.users import CreateUserSchema, UpdateUserSchema
from app.core.security import hash_password, verify_password
from app.api.exception_handlers import CRUDException
from sqlalchemy.ext.asyncio import AsyncSession

class UserCRUD(CRUDBase[Users, CreateUserSchema, UpdateUserSchema]):
    async def create(self, db: AsyncSession, obj_in: CreateUserSchema) -> Users:
        try:
            hashed = hash_password(obj_in.password)
            db_obj = self.model(username=obj_in.username, password=hashed)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            if "ix_users_username" in str(e):
                print(f"duplicate username in {self.model.__name__} create: {e}")
                raise CRUDException(self.model.__name__, f"duplicate username in create")
            print(f"error in {self.model.__name__} create: {e}")
            raise CRUDException(self.model.__name__, f"error in create: {e}")

    async def authenticate(self, db: AsyncSession, username: str, password: str) -> Users:
        user = await self.get_by_attribute(db, "username", username)
        if not user or not verify_password(password, user.password):
            print(f"error in {self.model.__name__} authenticate: incorrect password")
            raise CRUDException(self.model.__name__, f"error in authenticate: incorrect password", 401)
        return user

user_crud = UserCRUD(Users)
