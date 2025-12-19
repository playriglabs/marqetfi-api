"""Order repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderStatus
from app.models.trading import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Order repository."""

    def __init__(self) -> None:
        """Initialize order repository."""
        super().__init__(Order)

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        """Get all orders for user."""
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        user_id: int,
        status: OrderStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        """Get orders by status for user."""
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id, Order.status == status.value)
            .offset(skip)
            .limit(limit)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_provider_order_id(
        self, db: AsyncSession, provider: str, provider_order_id: str
    ) -> Order | None:
        """Get order by provider and provider order ID."""
        result = await db.execute(
            select(Order).where(
                Order.provider == provider, Order.provider_order_id == provider_order_id
            )
        )
        return result.scalar_one_or_none()  # type: ignore
