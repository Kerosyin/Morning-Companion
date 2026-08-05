from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, pk: Any) -> ModelType | None:
        """
        Retrieves an instance by its primary key.
        """
        return await self.session.get(self.model, pk)

    async def get_by(self, **kwargs) -> ModelType | None:
        """
        Retrieves the first instance matching the given criteria.
        """
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, **kwargs) -> ModelType:
        """
        Creates a new instance and adds it to the session.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """
        Updates an existing instance in the session.
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Marks an instance for deletion.
        """
        await self.session.delete(instance)
