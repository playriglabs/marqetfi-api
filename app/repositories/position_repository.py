"""Position repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trading import Position
from app.repositories.base import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """Position repository."""

    def __init__(self) -> None:
        """Initialize position repository."""
        super().__init__(Position)

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Position]:
        """Get all positions for user."""
        result = await db.execute(
            select(Position)
            .where(Position.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Position.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_trade_id(self, db: AsyncSession, trade_id: int) -> Position | None:
        """Get position by trade ID."""
        result = await db.execute(select(Position).where(Position.trade_id == trade_id))
        return result.scalar_one_or_none()  # type: ignore
