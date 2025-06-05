from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeMeta
from app.api.exception_handlers import CRUDException

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            obj = result.scalars().first()
            if obj is None:
                raise CRUDException(self.model.__name__, f"{self.model.__name__} with id {id} not found")
            return obj
        except Exception as e:
            await db.rollback()
            print(f"error in {self.model.__name__} get: {e}")
            raise CRUDException(self.model.__name__, f"error in get with id: {id}")

    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        try:
            result = await db.execute(select(self.model))
            return result.scalars().all()
        except Exception as e:
            await db.rollback()
            print(f"error in {self.model.__name__} get_all: {e}")
            raise CRUDException(self.model.__name__, f"error in get_all")

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType: 
        try:
            obj = self.model(**obj_in.model_dump())
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except Exception as e:
            await db.rollback()
            print(f"error in {self.model.__name__} create: {e}")
            raise CRUDException(self.model.__name__, f"error in create: {e}")

    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        try:
            obj_data = db_obj.__dict__
            update_data = obj_in.model_dump(exclude_unset=True)
            for field in update_data:
                if field in obj_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            print(f"error in {self.model.__name__} update: {e}")
            raise CRUDException(self.model.__name__, f"error in update: {e}")
    
    async def delete(self, db: AsyncSession, id: int) -> None:
        try:
            result = await db.execute(delete(self.model).where(self.model.id == id))
            if result.rowcount == 0:
                raise CRUDException(self.model.__name__, f"{self.model.__name__} with id {id} not found")
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"error in {self.model.__name__} delete: {e}")
            raise CRUDException(self.model.__name__, f"error in delete: {e}")
