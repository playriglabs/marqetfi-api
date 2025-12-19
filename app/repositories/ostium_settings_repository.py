"""Ostium settings repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ostium_settings import OstiumSettings
from app.repositories.base import BaseRepository


class OstiumSettingsRepository(BaseRepository[OstiumSettings]):
    """Repository for Ostium settings."""

    def __init__(self) -> None:
        """Initialize repository."""
        super().__init__(OstiumSettings)

    async def get_active(self, db: AsyncSession) -> OstiumSettings | None:
        """Get currently active settings.

        Args:
            db: Database session

        Returns:
            OstiumSettings if active settings exist, None otherwise
        """
        result = await db.execute(
            select(OstiumSettings)
            .where(OstiumSettings.is_active == True)  # noqa: E712
            .order_by(OstiumSettings.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_history(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OstiumSettings]:
        """Get settings history with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of OstiumSettings ordered by creation date (newest first)
        """
        result = await db.execute(
            select(OstiumSettings)
            .order_by(OstiumSettings.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_next_version(self, db: AsyncSession) -> int:
        """Get the next version number.

        Args:
            db: Database session

        Returns:
            int: Next version number (1 if no settings exist)
        """
        result = await db.execute(
            select(OstiumSettings.version).order_by(OstiumSettings.version.desc()).limit(1)
        )
        max_version = result.scalar_one_or_none()
        return (max_version or 0) + 1

    async def activate(self, db: AsyncSession, settings_id: int) -> OstiumSettings:
        """Activate a settings version and deactivate all others.

        Args:
            db: Database session
            settings_id: ID of settings to activate

        Returns:
            OstiumSettings: Activated settings

        Raises:
            ValueError: If settings not found
        """
        # Get the settings to activate
        settings = await self.get(db, settings_id)
        if not settings:
            raise ValueError(f"Settings with id {settings_id} not found")

        # Deactivate all other active settings
        result = await db.execute(
            select(OstiumSettings).where(OstiumSettings.is_active == True)  # noqa: E712
        )
        all_active = result.scalars().all()
        for active_setting in all_active:
            active_setting.is_active = False

        # Activate the requested settings
        settings.is_active = True
        await db.commit()
        await db.refresh(settings)
        return settings

    async def deactivate(self, db: AsyncSession, settings_id: int) -> OstiumSettings:
        """Deactivate a settings version.

        Args:
            db: Database session
            settings_id: ID of settings to deactivate

        Returns:
            OstiumSettings: Deactivated settings

        Raises:
            ValueError: If settings not found
        """
        settings = await self.get(db, settings_id)
        if not settings:
            raise ValueError(f"Settings with id {settings_id} not found")

        settings.is_active = False
        await db.commit()
        await db.refresh(settings)
        return settings
