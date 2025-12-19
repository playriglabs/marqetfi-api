"""Factory for creating wallet provider instances."""

from typing import Any

from app.config import get_settings
from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.exceptions import WalletProviderUnavailableError
from app.services.wallet_providers.registry import WalletProviderRegistry


class WalletProviderFactory:
    """Factory for creating wallet provider instances."""

    _provider_cache: dict[str, BaseWalletProvider] = {}

    @classmethod
    async def get_provider(cls, provider_name: str | None = None) -> BaseWalletProvider:
        """Get configured wallet provider instance.

        Args:
            provider_name: Optional provider name. If None, uses WALLET_PROVIDER from settings.

        Returns:
            Wallet provider instance

        Raises:
            WalletProviderUnavailableError: If provider is not found or not configured
        """
        if provider_name is None:
            settings = get_settings()
            provider_name = getattr(settings, "WALLET_PROVIDER", "none")

        if provider_name == "none":
            raise WalletProviderUnavailableError(
                "No wallet provider configured. Set WALLET_PROVIDER environment variable.",
                service_name="wallet_provider",
            )

        # Check cache
        if provider_name in cls._provider_cache:
            return cls._provider_cache[provider_name]

        # Get provider class
        provider_class = WalletProviderRegistry.get(provider_name)
        if not provider_class:
            available = WalletProviderRegistry.list_providers()
            raise WalletProviderUnavailableError(
                f"Wallet provider '{provider_name}' not found. "
                f"Available providers: {available}",
                service_name="wallet_provider",
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)

        # Initialize and cache
        await provider.initialize()
        cls._provider_cache[provider_name] = provider

        return provider

    @classmethod
    async def _get_provider_config(cls, provider_name: str, db_session: Any = None) -> Any:
        """Get provider configuration based on provider name.

        Tries to load from database first, falls back to environment variables.

        Args:
            provider_name: Provider name
            db_session: Optional database session

        Returns:
            Provider configuration object

        Raises:
            ValueError: If provider name is unknown
        """
        # Try to load from database first
        try:
            if db_session is not None:
                from app.services.configuration_service import ConfigurationService

                config_service = ConfigurationService(db_session)
                db_config = await config_service.get_provider_config(provider_name, "wallet")
                if db_config:
                    if provider_name == "privy":
                        from app.services.wallet_providers.privy.config import PrivyWalletConfig

                        return PrivyWalletConfig(**db_config)
                    elif provider_name == "dynamic":
                        from app.services.wallet_providers.dynamic.config import DynamicWalletConfig

                        return DynamicWalletConfig(**db_config)
            else:
                from app.core.database import get_session_maker

                session_maker = get_session_maker()
                async with session_maker() as session:
                    try:
                        from app.services.configuration_service import ConfigurationService

                        config_service = ConfigurationService(session)
                        db_config = await config_service.get_provider_config(
                            provider_name, "wallet"
                        )
                        if db_config:
                            if provider_name == "privy":
                                from app.services.wallet_providers.privy.config import (
                                    PrivyWalletConfig,
                                )

                                return PrivyWalletConfig(**db_config)
                            elif provider_name == "dynamic":
                                from app.services.wallet_providers.dynamic.config import (
                                    DynamicWalletConfig,
                                )

                                return DynamicWalletConfig(**db_config)
                    except Exception:
                        pass
        except Exception:
            pass

        # Fall back to environment variables
        settings = get_settings()

        if provider_name == "privy":
            from app.services.wallet_providers.privy.config import PrivyWalletConfig

            return PrivyWalletConfig(
                enabled=getattr(settings, "PRIVY_ENABLED", True),
                app_id=getattr(settings, "PRIVY_APP_ID", ""),
                app_secret=getattr(settings, "PRIVY_APP_SECRET", ""),
                environment=getattr(settings, "PRIVY_ENVIRONMENT", "production"),
                use_embedded_wallets=getattr(settings, "PRIVY_USE_EMBEDDED_WALLETS", True),
                timeout=getattr(settings, "PRIVY_TIMEOUT", 30),
                retry_attempts=getattr(settings, "PRIVY_RETRY_ATTEMPTS", 3),
                retry_delay=getattr(settings, "PRIVY_RETRY_DELAY", 1.0),
            )

        if provider_name == "dynamic":
            from app.services.wallet_providers.dynamic.config import DynamicWalletConfig

            return DynamicWalletConfig(
                enabled=getattr(settings, "DYNAMIC_ENABLED", True),
                api_key=getattr(settings, "DYNAMIC_API_KEY", ""),
                api_secret=getattr(settings, "DYNAMIC_API_SECRET", ""),
                api_url=getattr(settings, "DYNAMIC_API_URL", "https://api.dynamic.xyz"),
                environment=getattr(settings, "DYNAMIC_ENVIRONMENT", "production"),
                timeout=getattr(settings, "DYNAMIC_TIMEOUT", 30),
                retry_attempts=getattr(settings, "DYNAMIC_RETRY_ATTEMPTS", 3),
                retry_delay=getattr(settings, "DYNAMIC_RETRY_DELAY", 1.0),
            )

        raise ValueError(f"Unknown wallet provider: {provider_name}")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear provider cache."""
        cls._provider_cache.clear()
