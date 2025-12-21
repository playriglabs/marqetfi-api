"""Factory for creating provider instances."""

from typing import Any

from app.config.providers.lifi import LifiConfig
from app.config.providers.lighter import LighterConfig
from app.config.providers.ostium import OstiumConfig

# Import providers to trigger auto-registration
from app.services.providers import auth0, lifi, lighter, ostium, privy, symbiosis  # noqa: F401
from app.services.providers.auth0.config import Auth0AuthConfig
from app.services.providers.base import (
    BaseAuthProvider,
    BasePriceProvider,
    BaseSettlementProvider,
    BaseSwapProvider,
    BaseTradingProvider,
)
from app.services.providers.exceptions import ExternalServiceError
from app.services.providers.privy.config import PrivyAuthConfig
from app.services.providers.registry import ProviderRegistry


class ProviderFactory:
    """Factory for creating provider instances."""

    _trading_provider_cache: dict[str, BaseTradingProvider] = {}
    _price_provider_cache: dict[str, BasePriceProvider] = {}
    _settlement_provider_cache: dict[str, BaseSettlementProvider] = {}
    _swap_provider_cache: dict[str, BaseSwapProvider] = {}
    _auth_provider_cache: dict[str, BaseAuthProvider] = {}

    @classmethod
    async def _get_provider_config(cls, provider_name: str, db_session: Any = None) -> Any:
        """Get provider configuration based on provider name.

        Tries to load from database first, falls back to environment variables.

        Args:
            provider_name: Name of the provider
            db_session: Optional database session for loading from database

        Returns:
            Provider configuration instance
        """
        # This would be extended to support multiple providers
        if provider_name == "ostium":
            # Try to load from database first
            try:
                # Use provided session or create a temporary one
                if db_session is not None:
                    from app.services.ostium_admin_service import OstiumAdminService

                    service = OstiumAdminService()
                    db_config = await service.get_active_config(db_session)
                    if db_config:
                        return db_config
                else:
                    # Create temporary session for loading config
                    from app.core.database import get_session_maker

                    session_maker = get_session_maker()
                    async with session_maker() as session:
                        try:
                            from app.services.ostium_admin_service import OstiumAdminService

                            service = OstiumAdminService()
                            db_config = await service.get_active_config(session)
                            if db_config:
                                return db_config
                        except Exception:
                            # If database load fails, fall back to environment
                            pass
            except Exception:
                # If we can't even create a session, fall back to environment
                pass

            # Fall back to environment variables
            from app.config import get_settings

            settings = get_settings()
            # Use new format if available, fall back to old format for backward compatibility
            private_key = (
                settings.ostium_private_key
                if hasattr(settings, "ostium_private_key") and settings.ostium_private_key
                else settings.private_key
            )
            rpc_url = (
                settings.ostium_rpc_url
                if hasattr(settings, "ostium_rpc_url") and settings.ostium_rpc_url
                else settings.rpc_url
            )
            network = (
                settings.ostium_network
                if hasattr(settings, "ostium_network") and settings.ostium_network
                else settings.network
            )

            # Get wallet provider settings
            wallet_provider = getattr(settings, "WALLET_PROVIDER", "none")
            use_wallet_provider = getattr(settings, "OSTIUM_USE_WALLET_PROVIDER", False)
            wallet_provider_id = getattr(settings, "OSTIUM_WALLET_PROVIDER_ID", None)
            fallback_to_private_key = getattr(settings, "OSTIUM_FALLBACK_TO_PRIVATE_KEY", True)

            return OstiumConfig(
                enabled=getattr(settings, "ostium_enabled", True),
                private_key=private_key,
                rpc_url=rpc_url,
                network=network,
                verbose=getattr(settings, "ostium_verbose", False),
                slippage_percentage=getattr(settings, "ostium_slippage_percentage", 1.0),
                timeout=getattr(settings, "ostium_timeout", 30),
                retry_attempts=getattr(settings, "ostium_retry_attempts", 3),
                retry_delay=getattr(settings, "ostium_retry_delay", 1.0),
                wallet_provider=wallet_provider if wallet_provider != "none" else None,
                wallet_provider_id=wallet_provider_id,
                use_wallet_provider=use_wallet_provider,
                fallback_to_private_key=fallback_to_private_key,
            )

        if provider_name == "lighter":
            # Try to load from database first
            try:
                if db_session is not None:
                    from app.services.configuration_service import ConfigurationService

                    config_service = ConfigurationService(db_session)
                    lighter_db_config: dict[str, Any] | None = (
                        await config_service.get_provider_config("lighter", "trading")
                    )
                    if lighter_db_config:
                        return LighterConfig(**lighter_db_config)
                else:
                    from app.core.database import get_session_maker

                    session_maker = get_session_maker()
                    async with session_maker() as session:
                        try:
                            from app.services.configuration_service import ConfigurationService

                            config_service = ConfigurationService(session)
                            lighter_db_config_session: dict[str, Any] | None = (
                                await config_service.get_provider_config("lighter", "trading")
                            )
                            if lighter_db_config_session:
                                return LighterConfig(**lighter_db_config_session)
                        except Exception:
                            pass
            except Exception:
                pass

            # Fall back to environment variables
            from app.config import get_settings

            settings = get_settings()

            return LighterConfig(
                enabled=getattr(settings, "lighter_enabled", True),
                api_url=getattr(settings, "lighter_api_url", "https://api.lighter.xyz"),
                api_key=getattr(settings, "lighter_api_key", None),
                private_key=getattr(settings, "lighter_private_key", None),
                network=getattr(settings, "lighter_network", "mainnet"),
                timeout=getattr(settings, "lighter_timeout", 30),
                retry_attempts=getattr(settings, "lighter_retry_attempts", 3),
                retry_delay=getattr(settings, "lighter_retry_delay", 1.0),
            )

        if provider_name == "lifi":
            # Try to load from database first
            try:
                if db_session is not None:
                    from app.services.configuration_service import ConfigurationService

                    config_service = ConfigurationService(db_session)
                    lifi_db_config: dict[str, Any] | None = (
                        await config_service.get_provider_config("lifi", "swap")
                    )
                    if lifi_db_config:
                        return LifiConfig(**lifi_db_config)
                else:
                    from app.core.database import get_session_maker

                    session_maker = get_session_maker()
                    async with session_maker() as session:
                        try:
                            from app.services.configuration_service import ConfigurationService

                            config_service = ConfigurationService(session)
                            lifi_db_config_session: dict[str, Any] | None = (
                                await config_service.get_provider_config("lifi", "swap")
                            )
                            if lifi_db_config_session:
                                return LifiConfig(**lifi_db_config_session)
                        except Exception:
                            pass
            except Exception:
                pass

            # Fall back to environment variables
            from app.config import get_settings

            settings = get_settings()

            return LifiConfig(
                enabled=getattr(settings, "lifi_enabled", True),
                api_url=getattr(settings, "LIFI_API_URL", "https://li.xyz/v1"),
                api_key=getattr(settings, "LIFI_API_KEY", None),
                timeout=getattr(settings, "lifi_timeout", 30),
                retry_attempts=getattr(settings, "lifi_retry_attempts", 3),
                retry_delay=getattr(settings, "lifi_retry_delay", 1.0),
            )

        if provider_name == "auth0":
            # Auth0 auth provider config
            from app.config import get_settings

            settings = get_settings()
            return Auth0AuthConfig(
                enabled=getattr(settings, "AUTH0_DOMAIN", "") != "",
                domain=getattr(settings, "AUTH0_DOMAIN", ""),
                client_id=getattr(settings, "AUTH0_CLIENT_ID", ""),
                client_secret=getattr(settings, "AUTH0_CLIENT_SECRET", ""),
                audience=getattr(settings, "AUTH0_AUDIENCE", ""),
                management_client_id=getattr(settings, "AUTH0_MANAGEMENT_CLIENT_ID", ""),
                management_client_secret=getattr(settings, "AUTH0_MANAGEMENT_CLIENT_SECRET", ""),
                algorithm=getattr(settings, "AUTH0_ALGORITHM", "RS256"),
                timeout=30,
                retry_attempts=3,
                retry_delay=1.0,
            )

        if provider_name == "privy":
            # Privy auth provider config
            from app.config import get_settings

            settings = get_settings()
            return PrivyAuthConfig(
                enabled=getattr(settings, "PRIVY_ENABLED", True),
                app_id=getattr(settings, "PRIVY_APP_ID", ""),
                app_secret=getattr(settings, "PRIVY_APP_SECRET", ""),
                environment=getattr(settings, "PRIVY_ENVIRONMENT", "production"),
                timeout=getattr(settings, "PRIVY_TIMEOUT", 30),
                retry_attempts=getattr(settings, "PRIVY_RETRY_ATTEMPTS", 3),
                retry_delay=getattr(settings, "PRIVY_RETRY_DELAY", 1.0),
            )

        raise ValueError(f"Unknown provider: {provider_name}")

    @classmethod
    async def get_trading_provider(cls, provider_name: str | None = None) -> BaseTradingProvider:
        """Get configured trading provider instance."""
        if provider_name is None:
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "TRADING_PROVIDER", "ostium")

        # Check cache
        if provider_name in cls._trading_provider_cache:
            return cls._trading_provider_cache[provider_name]

        # Get provider class
        provider_class = ProviderRegistry.get_trading_provider(provider_name)
        if not provider_class:
            raise ExternalServiceError(
                f"Trading provider '{provider_name}' not found. "
                f"Available: {ProviderRegistry.list_trading_providers()}"
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)  # type: ignore[arg-type]

        # Initialize and cache
        await provider.initialize()
        cls._trading_provider_cache[provider_name] = provider

        return provider

    @classmethod
    async def get_price_provider(cls, provider_name: str | None = None) -> BasePriceProvider:
        """Get configured price provider instance."""
        if provider_name is None:
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "PRICE_PROVIDER", "ostium")

        # Check cache
        if provider_name in cls._price_provider_cache:
            return cls._price_provider_cache[provider_name]

        # Get provider class
        provider_class = ProviderRegistry.get_price_provider(provider_name)
        if not provider_class:
            raise ExternalServiceError(
                f"Price provider '{provider_name}' not found. "
                f"Available: {ProviderRegistry.list_price_providers()}"
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)  # type: ignore[arg-type]

        # Initialize and cache
        await provider.initialize()
        cls._price_provider_cache[provider_name] = provider

        return provider

    @classmethod
    async def get_settlement_provider(
        cls, provider_name: str | None = None
    ) -> BaseSettlementProvider:
        """Get configured settlement provider instance."""
        if provider_name is None:
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "SETTLEMENT_PROVIDER", "ostium")

        # Check cache
        if provider_name in cls._settlement_provider_cache:
            return cls._settlement_provider_cache[provider_name]

        # Get provider class
        provider_class = ProviderRegistry.get_settlement_provider(provider_name)
        if not provider_class:
            raise ExternalServiceError(
                f"Settlement provider '{provider_name}' not found. "
                f"Available: {ProviderRegistry.list_settlement_providers()}"
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)  # type: ignore[arg-type]

        # Initialize and cache
        await provider.initialize()
        cls._settlement_provider_cache[provider_name] = provider

        return provider

    @classmethod
    async def get_swap_provider(cls, provider_name: str | None = None) -> BaseSwapProvider:
        """Get configured swap provider instance."""
        if provider_name is None:
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "SWAP_PROVIDER", "lifi")

        # Check cache
        if provider_name in cls._swap_provider_cache:
            return cls._swap_provider_cache[provider_name]

        # Get provider class
        provider_class = ProviderRegistry.get_swap_provider(provider_name)
        if not provider_class:
            raise ExternalServiceError(
                f"Swap provider '{provider_name}' not found. "
                f"Available: {ProviderRegistry.list_swap_providers()}"
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)  # type: ignore[arg-type]

        # Initialize and cache
        await provider.initialize()
        cls._swap_provider_cache[provider_name] = provider

        return provider

    @classmethod
    async def get_auth_provider(cls, provider_name: str | None = None) -> BaseAuthProvider:
        """Get configured authentication provider instance."""
        if provider_name is None:
            from app.config import get_settings

            settings = get_settings()
            # Default to privy if enabled, otherwise auth0
            if getattr(settings, "PRIVY_ENABLED", False) and getattr(settings, "PRIVY_APP_ID", ""):
                provider_name = "privy"
            elif getattr(settings, "AUTH0_DOMAIN", ""):
                provider_name = "auth0"
            else:
                raise ExternalServiceError(
                    "No authentication provider configured. "
                    "Set PRIVY_APP_ID or AUTH0_DOMAIN environment variables."
                )

        # Check cache
        if provider_name in cls._auth_provider_cache:
            return cls._auth_provider_cache[provider_name]

        # Get provider class
        provider_class = ProviderRegistry.get_auth_provider(provider_name)
        if not provider_class:
            raise ExternalServiceError(
                f"Authentication provider '{provider_name}' not found. "
                f"Available: {ProviderRegistry.list_auth_providers()}"
            )

        # Get config and create instance
        config = await cls._get_provider_config(provider_name, db_session=None)
        provider = provider_class(config)  # type: ignore[arg-type]

        # Initialize and cache
        await provider.initialize()
        cls._auth_provider_cache[provider_name] = provider

        return provider
