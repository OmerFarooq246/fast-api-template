from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base


class Repository[
    ModelType: Base,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
]:
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, object_id: int) -> ModelType | None:
        return await session.get(self.model, object_id)

    async def get_by_attribute(
        self,
        session: AsyncSession,
        attribute: str,
        value: Any,
    ) -> list[ModelType]:
        column = getattr(self.model, attribute, None)
        if column is None:
            raise ValueError(f"Unknown attribute {attribute!r} for {self.model.__name__}")

        result = await session.scalars(select(self.model).where(column == value))
        return list(result.all())

    async def list(self, session: AsyncSession) -> list[ModelType]:
        result = await session.scalars(select(self.model).order_by(self.model.id.asc()))
        return list(result.all())

    async def create(
        self,
        session: AsyncSession,
        data: CreateSchemaType,
    ) -> ModelType:
        instance = self.model(**data.model_dump())
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(
        self,
        session: AsyncSession,
        instance: ModelType,
        data: UpdateSchemaType,
    ) -> ModelType:
        for field, value in data.model_dump(exclude_unset=True).items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, instance: ModelType) -> None:
        await session.delete(instance)
        await session.flush()
