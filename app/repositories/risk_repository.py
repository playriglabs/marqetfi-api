"""Risk repository."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import RiskEvent, RiskLimit
from app.repositories.base import BaseRepository


class RiskLimitRepository(BaseRepository[RiskLimit]):
    """Risk limit repository."""

    def __init__(self) -> None:
        """Initialize risk limit repository."""
        super().__init__(RiskLimit)

    async def get_by_user(
        self, db: AsyncSession, user_id: int, asset: str | None = None
    ) -> RiskLimit | None:
        """Get risk limit for user and optional asset.

        Args:
            db: Database session
            user_id: User ID
            asset: Optional asset filter

        Returns:
            Risk limit or None
        """
        query = select(RiskLimit).where(
            RiskLimit.user_id == user_id,
            RiskLimit.is_active == True,  # noqa: E712
        )
        if asset:
            query = query.where(RiskLimit.asset == asset)
        else:
            query = query.where(RiskLimit.asset.is_(None))

        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_asset(self, db: AsyncSession, asset: str) -> RiskLimit | None:
        """Get global risk limit for asset.

        Args:
            db: Database session
            asset: Asset symbol

        Returns:
            Risk limit or None
        """
        result = await db.execute(
            select(RiskLimit).where(
                RiskLimit.user_id.is_(None),
                RiskLimit.asset == asset,
                RiskLimit.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_global_default(self, db: AsyncSession) -> RiskLimit | None:
        """Get global default risk limit.

        Args:
            db: Database session

        Returns:
            Risk limit or None
        """
        result = await db.execute(
            select(RiskLimit).where(
                RiskLimit.user_id.is_(None),
                RiskLimit.asset.is_(None),
                RiskLimit.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_all_active(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[RiskLimit]:
        """Get all active risk limits.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of risk limits
        """
        result = await db.execute(
            select(RiskLimit)
            .where(RiskLimit.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .order_by(RiskLimit.created_at.desc())
        )
        return list(result.scalars().all())


class RiskEventRepository(BaseRepository[RiskEvent]):
    """Risk event repository."""

    def __init__(self) -> None:
        """Initialize risk event repository."""
        super().__init__(RiskEvent)

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RiskEvent]:
        """Get risk events for user.

        Args:
            db: Database session
            user_id: User ID
            event_type: Optional event type filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of risk events
        """
        query = select(RiskEvent).where(RiskEvent.user_id == user_id)
        if event_type:
            query = query.where(RiskEvent.event_type == event_type)

        result = await db.execute(
            query.offset(skip).limit(limit).order_by(RiskEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_event(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str,
        threshold: Decimal,
        current_value: Decimal,
        severity: str = "warning",
        message: str | None = None,
        position_id: int | None = None,
    ) -> RiskEvent:
        """Create a new risk event.

        Args:
            db: Database session
            user_id: User ID
            event_type: Event type
            threshold: Threshold value
            current_value: Current value
            severity: Event severity (warning, critical, alert)
            message: Optional message
            position_id: Optional position ID

        Returns:
            Created risk event
        """
        event = await self.create(
            db,
            {
                "user_id": user_id,
                "event_type": event_type,
                "threshold": threshold,
                "current_value": current_value,
                "severity": severity,
                "message": message,
                "position_id": position_id,
            },
        )
        return event  # type: ignore
