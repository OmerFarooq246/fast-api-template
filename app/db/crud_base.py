from typing import Any

from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.exceptions import (
    ApplicationError,
    PersistenceError,
    ResourceNotFoundError,
)
from app.db.database import Base


class CRUDBase[
    ModelType: Base,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
]:
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType:
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            obj = result.scalars().first()
            if obj is None:
                raise ResourceNotFoundError(self.model.__name__, id)
            return obj
        except ApplicationError:
            raise
        except Exception as e:
            await db.rollback()
            raise PersistenceError(self.model.__name__, "get") from e

    async def get_by_attribute(
        self, db: AsyncSession, attr: str, value: Any, all: bool = False
    ) -> list[ModelType]:
        try:
            column = getattr(self.model, attr, None)
            if column is None:
                raise ValueError(f"Unknown attribute {attr!r} for {self.model.__name__}")

            stmt = select(self.model).where(column == value)
            result = await db.execute(stmt)
            if all:
                objects = result.scalars().all()
                return list(objects)
            else:
                object_ = result.scalars().first()
                if object_ is None:
                    raise ResourceNotFoundError(self.model.__name__, f"{attr}={value}")
                return [object_]
        except ApplicationError:
            raise
        except Exception as e:
            await db.rollback()
            raise PersistenceError(self.model.__name__, "get by attribute") from e

    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        try:
            stmt = select(self.model).order_by(self.model.id.asc())
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise PersistenceError(self.model.__name__, "list") from e

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        try:
            obj = self.model(**obj_in.model_dump())
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except Exception as e:
            await db.rollback()
            raise PersistenceError(self.model.__name__, "create") from e

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
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
            raise PersistenceError(self.model.__name__, "update") from e

    async def delete(self, db: AsyncSession, id: int) -> None:
        try:
            result = await db.execute(delete(self.model).where(self.model.id == id))
            if result.rowcount == 0:  # type: ignore[attr-defined]
                raise ResourceNotFoundError(self.model.__name__, id)
            await db.commit()
        except ApplicationError:
            raise
        except Exception as e:
            await db.rollback()
            raise PersistenceError(self.model.__name__, "delete") from e
