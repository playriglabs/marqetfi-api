"""Base repository."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):  # noqa: UP046
    """Base repository for common CRUD operations."""

    def __init__(self, model: type[ModelType]) -> None:
        """Initialize repository."""
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Get record by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))  # type: ignore[attr-defined]
        return result.scalar_one_or_none()  # type: ignore

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get all records with pagination."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: dict[str, Any]) -> ModelType:
        """Create new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        """Update existing record."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: Any) -> bool:
        """Delete record by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))  # type: ignore[attr-defined]
        db_obj = result.scalar_one_or_none()  # type: ignore[assignment]
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False
