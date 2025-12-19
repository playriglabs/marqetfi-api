"""Repository for application configuration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_configuration import AppConfiguration, ProviderConfiguration
from app.repositories.base import BaseRepository


class AppConfigurationRepository(BaseRepository[AppConfiguration]):
    """Repository for app configuration operations."""

    def __init__(self) -> None:
        """Initialize repository."""
        super().__init__(AppConfiguration)

    async def get_by_key(self, db: AsyncSession, key: str) -> AppConfiguration | None:
        """Get configuration by key."""
        result = await db.execute(
            select(AppConfiguration).where(
                AppConfiguration.config_key == key,
                AppConfiguration.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, db: AsyncSession, category: str) -> list[AppConfiguration]:
        """Get all configurations by category."""
        result = await db.execute(
            select(AppConfiguration).where(
                AppConfiguration.category == category,
                AppConfiguration.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_all_active(self, db: AsyncSession) -> list[AppConfiguration]:
        """Get all active configurations."""
        result = await db.execute(
            select(AppConfiguration).where(AppConfiguration.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())


class ProviderConfigurationRepository(BaseRepository[ProviderConfiguration]):
    """Repository for provider configuration operations."""

    def __init__(self) -> None:
        """Initialize repository."""
        super().__init__(ProviderConfiguration)

    async def get_active_config(
        self, db: AsyncSession, provider_name: str, provider_type: str
    ) -> ProviderConfiguration | None:
        """Get active configuration for a provider."""
        result = await db.execute(
            select(ProviderConfiguration).where(
                ProviderConfiguration.provider_name == provider_name,
                ProviderConfiguration.provider_type == provider_type,
                ProviderConfiguration.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(
        self, db: AsyncSession, provider_name: str
    ) -> list[ProviderConfiguration]:
        """Get all configurations for a provider."""
        result = await db.execute(
            select(ProviderConfiguration).where(
                ProviderConfiguration.provider_name == provider_name
            )
        )
        return list(result.scalars().all())

    async def get_latest_version(
        self, db: AsyncSession, provider_name: str, provider_type: str
    ) -> ProviderConfiguration | None:
        """Get latest version of configuration (active or not)."""
        result = await db.execute(
            select(ProviderConfiguration)
            .where(
                ProviderConfiguration.provider_name == provider_name,
                ProviderConfiguration.provider_type == provider_type,
            )
            .order_by(ProviderConfiguration.version.desc())
        )
        return result.scalar_one_or_none()
