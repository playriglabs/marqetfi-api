"""Trade repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TradeStatus
from app.models.trading import Trade
from app.repositories.base import BaseRepository


class TradeRepository(BaseRepository[Trade]):
    """Trade repository."""

    def __init__(self) -> None:
        """Initialize trade repository."""
        super().__init__(Trade)

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Trade]:
        """Get all trades for user."""
        result = await db.execute(
            select(Trade)
            .where(Trade.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Trade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        user_id: int,
        status: TradeStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        """Get trades by status for user."""
        result = await db.execute(
            select(Trade)
            .where(Trade.user_id == user_id, Trade.status == status.value)
            .offset(skip)
            .limit(limit)
            .order_by(Trade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_provider_trade_id(
        self, db: AsyncSession, provider: str, provider_trade_id: str
    ) -> Trade | None:
        """Get trade by provider and provider trade ID."""
        result = await db.execute(
            select(Trade).where(
                Trade.provider == provider, Trade.provider_trade_id == provider_trade_id
            )
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_pair_and_index(
        self, db: AsyncSession, pair_id: int, trade_index: int
    ) -> Trade | None:
        """Get trade by pair ID and trade index."""
        result = await db.execute(
            select(Trade).where(Trade.pair_id == pair_id, Trade.trade_index == trade_index)
        )
        return result.scalar_one_or_none()  # type: ignore
