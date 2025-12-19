"""Configuration service for loading settings from database with env fallback."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.app_configuration_repository import (
    AppConfigurationRepository,
    ProviderConfigurationRepository,
)
from app.utils.encryption import decrypt_value


class ConfigurationService:
    """Service for managing application and provider configurations."""

    def __init__(self, db: AsyncSession | None = None):
        """Initialize configuration service.

        Args:
            db: Optional database session. If None, will create temporary session when needed.
        """
        self.db = db
        self.app_config_repo = AppConfigurationRepository()
        self.provider_config_repo = ProviderConfigurationRepository()

    async def get_app_config(self, key: str, default: Any = None) -> Any:
        """Get application configuration value by key.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        if self.db:
            config = await self.app_config_repo.get_by_key(self.db, key)
            if config:
                value = config.config_value
                if config.is_encrypted:
                    value = decrypt_value(value)
                return self._convert_value(value, config.config_type)
        return default

    async def get_provider_config(
        self, provider_name: str, provider_type: str
    ) -> dict[str, Any] | None:
        """Get provider configuration from database.

        Args:
            provider_name: Provider name (ostium, lighter, lifi, etc.)
            provider_type: Provider type (trading, price, settlement, swap, wallet)

        Returns:
            Configuration dictionary or None
        """
        if self.db:
            config = await self.provider_config_repo.get_active_config(
                self.db, provider_name, provider_type
            )
            if config:
                return config.config_data
        return None

    async def get_all_app_configs(self, category: str | None = None) -> dict[str, Any]:
        """Get all application configurations.

        Args:
            category: Optional category filter

        Returns:
            Dictionary of config_key -> config_value
        """
        if not self.db:
            return {}

        if category:
            configs = await self.app_config_repo.get_by_category(self.db, category)
        else:
            configs = await self.app_config_repo.get_all_active(self.db)

        result = {}
        for config in configs:
            value = config.config_value
            if config.is_encrypted:
                value = decrypt_value(value)
            result[config.config_key] = self._convert_value(value, config.config_type)

        return result

    def _convert_value(self, value: str | None, config_type: str) -> Any:
        """Convert string value to appropriate type.

        Args:
            value: String value
            config_type: Type (string, int, float, bool, json)

        Returns:
            Converted value
        """
        if value is None:
            return None

        if config_type == "int":
            try:
                return int(value)
            except ValueError:
                return 0
        elif config_type == "float":
            try:
                return float(value)
            except ValueError:
                return 0.0
        elif config_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif config_type == "json":
            import json

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            return value

    @staticmethod
    def get_env_config(key: str, default: Any = None) -> Any:
        """Get configuration from environment variables (fallback).

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Configuration value or default
        """
        settings = get_settings()
        return getattr(settings, key, default)

    async def get_config_with_fallback(
        self, key: str, default: Any = None, use_db: bool = True
    ) -> Any:
        """Get configuration with database first, then environment fallback.

        Args:
            key: Configuration key
            default: Default value if not found in DB or env
            use_db: Whether to check database first

        Returns:
            Configuration value
        """
        # Try database first if enabled
        if use_db and self.db:
            db_value = await self.get_app_config(key)
            if db_value is not None:
                return db_value

        # Fallback to environment
        env_value = self.get_env_config(key)
        if env_value is not None:
            return env_value

        return default
