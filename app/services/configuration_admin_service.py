"""Admin service for managing configurations."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_configuration import AppConfiguration, ProviderConfiguration
from app.repositories.app_configuration_repository import (
    AppConfigurationRepository,
    ProviderConfigurationRepository,
)
from app.utils.encryption import decrypt_value, encrypt_value


class ConfigurationAdminService:
    """Service for managing configurations via admin API."""

    def __init__(self) -> None:
        """Initialize service."""
        self.app_config_repo = AppConfigurationRepository()
        self.provider_config_repo = ProviderConfigurationRepository()

    async def create_app_config(
        self,
        db: AsyncSession,
        config_data: dict[str, Any],
        created_by: int,
    ) -> AppConfiguration:
        """Create new app configuration.

        Args:
            db: Database session
            config_data: Configuration data
            created_by: User ID who created this

        Returns:
            Created configuration
        """
        # Encrypt value if needed
        config_value = config_data.get("config_value", "")
        if config_data.get("is_encrypted", False) and config_value:
            config_value = encrypt_value(config_value)

        config = await self.app_config_repo.create(
            db,
            {
                **config_data,
                "config_value": config_value,
                "created_by": created_by,
            },
        )
        return config

    async def update_app_config(
        self,
        db: AsyncSession,
        config_id: int,
        config_data: dict[str, Any],
    ) -> AppConfiguration:
        """Update app configuration.

        Args:
            db: Database session
            config_id: Configuration ID
            config_data: Updated configuration data

        Returns:
            Updated configuration
        """
        config = await self.app_config_repo.get(db, config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        # Handle encryption if value is being updated
        if "config_value" in config_data:
            if config_data.get("is_encrypted", config.is_encrypted):
                config_data["config_value"] = encrypt_value(config_data["config_value"])

        return await self.app_config_repo.update(db, config, config_data)

    async def create_provider_config(
        self,
        db: AsyncSession,
        config_data: dict[str, Any],
        created_by: int,
        activate: bool = True,
    ) -> ProviderConfiguration:
        """Create new provider configuration.

        Args:
            db: Database session
            config_data: Configuration data
            created_by: User ID who created this
            activate: Whether to activate this configuration

        Returns:
            Created configuration
        """
        provider_name = config_data["provider_name"]
        provider_type = config_data["provider_type"]

        # Get latest version
        latest = await self.provider_config_repo.get_latest_version(
            db, provider_name, provider_type
        )
        new_version = (latest.version + 1) if latest else 1

        # Deactivate all existing configs if activating new one
        if activate:
            existing = await self.provider_config_repo.get_active_config(
                db, provider_name, provider_type
            )
            if existing:
                await self.provider_config_repo.update(db, existing, {"is_active": False})

        config = await self.provider_config_repo.create(
            db,
            {
                **config_data,
                "version": new_version,
                "is_active": activate,
                "created_by": created_by,
            },
        )
        return config

    async def activate_provider_config(
        self,
        db: AsyncSession,
        config_id: int,
    ) -> ProviderConfiguration:
        """Activate a provider configuration.

        Args:
            db: Database session
            config_id: Configuration ID

        Returns:
            Activated configuration
        """
        config = await self.provider_config_repo.get(db, config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        # Deactivate all other configs for this provider/type
        existing = await self.provider_config_repo.get_active_config(
            db, config.provider_name, config.provider_type
        )
        if existing and existing.id != config_id:
            await self.provider_config_repo.update(db, existing, {"is_active": False})

        # Activate this config
        return await self.provider_config_repo.update(db, config, {"is_active": True})

    def config_to_dict(
        self, config: AppConfiguration, include_encrypted: bool = False
    ) -> dict[str, Any]:
        """Convert AppConfiguration to dictionary.

        Args:
            config: Configuration model
            include_encrypted: Whether to include encrypted values

        Returns:
            Configuration dictionary
        """
        value = config.config_value
        if config.is_encrypted and not include_encrypted:
            value = "***ENCRYPTED***"
        elif config.is_encrypted and include_encrypted:
            value = decrypt_value(value)

        return {
            "id": config.id,
            "config_key": config.config_key,
            "config_value": value,
            "config_type": config.config_type,
            "category": config.category,
            "description": config.description,
            "is_encrypted": config.is_encrypted,
            "is_active": config.is_active,
            "created_by": config.created_by,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }
