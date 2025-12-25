"""Extended tests for WalletProviderFactory."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.wallet_providers.exceptions import WalletProviderUnavailableError
from app.services.wallet_providers.factory import WalletProviderFactory


class TestWalletProviderFactoryExtended:
    """Extended tests for WalletProviderFactory."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear provider cache before each test."""
        WalletProviderFactory._provider_cache.clear()
        yield
        WalletProviderFactory._provider_cache.clear()

    @pytest.mark.asyncio
    async def test_get_provider_none_configured(self):
        """Test getting provider when none configured."""
        with patch("app.services.wallet_providers.factory.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.WALLET_PROVIDER = "none"
            mock_get_settings.return_value = mock_settings

            with pytest.raises(
                WalletProviderUnavailableError, match="No wallet provider configured"
            ):
                await WalletProviderFactory.get_provider()

    @pytest.mark.asyncio
    async def test_get_provider_default_from_settings(self):
        """Test getting provider using default from settings."""
        with (
            patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry,
            patch(
                "app.services.wallet_providers.factory.WalletProviderFactory._get_provider_config"
            ) as mock_get_config,
            patch("app.services.wallet_providers.factory.get_settings") as mock_get_settings,
        ):
            mock_settings = MagicMock()
            mock_settings.WALLET_PROVIDER = "privy"
            mock_get_settings.return_value = mock_settings

            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock()
            mock_provider_instance.initialize = AsyncMock()
            mock_provider_class.return_value = mock_provider_instance
            mock_registry.get.return_value = mock_provider_class
            mock_get_config.return_value = MagicMock()

            provider = await WalletProviderFactory.get_provider()

            assert provider == mock_provider_instance
            mock_registry.get.assert_called_once_with("privy")

    @pytest.mark.asyncio
    async def test_get_provider_config_from_db_session(self):
        """Test getting provider config from database session."""
        mock_db_session = MagicMock()
        mock_config_service = MagicMock()
        mock_config_service.get_provider_config = AsyncMock(
            return_value={"app_id": "test_id", "app_secret": "test_secret", "enabled": True}
        )

        with (
            patch(
                "app.services.wallet_providers.factory.ConfigurationService",
                return_value=mock_config_service,
            ),
            patch("app.services.wallet_providers.factory.PrivyWalletConfig") as mock_config_class,
        ):
            mock_config_instance = MagicMock()
            mock_config_class.return_value = mock_config_instance

            config = await WalletProviderFactory._get_provider_config(
                "privy", db_session=mock_db_session
            )

            assert config == mock_config_instance
            mock_config_service.get_provider_config.assert_called_once_with("privy", "wallet")

    @pytest.mark.asyncio
    async def test_get_provider_config_from_db_no_session(self):
        """Test getting provider config from database without session."""
        mock_config_service = MagicMock()
        mock_config_service.get_provider_config = AsyncMock(
            return_value={"api_key": "test_key", "api_secret": "test_secret", "enabled": True}
        )

        with (
            patch(
                "app.services.wallet_providers.factory.get_session_maker"
            ) as mock_get_session_maker,
            patch(
                "app.services.wallet_providers.factory.ConfigurationService",
                return_value=mock_config_service,
            ),
            patch("app.services.wallet_providers.factory.DynamicWalletConfig") as mock_config_class,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker = MagicMock(return_value=mock_session)
            mock_get_session_maker.return_value = mock_session_maker

            mock_config_instance = MagicMock()
            mock_config_class.return_value = mock_config_instance

            config = await WalletProviderFactory._get_provider_config("dynamic", db_session=None)

            assert config == mock_config_instance

    @pytest.mark.asyncio
    async def test_get_provider_config_fallback_to_env(self):
        """Test getting provider config falling back to environment."""
        with (
            patch(
                "app.services.wallet_providers.factory.get_session_maker",
                side_effect=Exception("No DB"),
            ),
            patch("app.services.wallet_providers.factory.get_settings") as mock_get_settings,
            patch("app.services.wallet_providers.factory.PrivyWalletConfig") as mock_config_class,
        ):
            mock_settings = MagicMock()
            mock_settings.PRIVY_ENABLED = True
            mock_settings.PRIVY_APP_ID = "test_id"
            mock_settings.PRIVY_APP_SECRET = "test_secret"
            mock_settings.PRIVY_ENVIRONMENT = "production"
            mock_settings.PRIVY_USE_EMBEDDED_WALLETS = True
            mock_settings.PRIVY_TIMEOUT = 30
            mock_settings.PRIVY_RETRY_ATTEMPTS = 3
            mock_settings.PRIVY_RETRY_DELAY = 1.0
            mock_get_settings.return_value = mock_settings

            mock_config_instance = MagicMock()
            mock_config_class.return_value = mock_config_instance

            config = await WalletProviderFactory._get_provider_config("privy", db_session=None)

            assert config == mock_config_instance

    @pytest.mark.asyncio
    async def test_get_provider_config_unknown_provider(self):
        """Test getting config for unknown provider."""
        with patch(
            "app.services.wallet_providers.factory.get_session_maker",
            side_effect=Exception("No DB"),
        ):
            with pytest.raises(ValueError, match="Unknown wallet provider"):
                await WalletProviderFactory._get_provider_config("unknown", db_session=None)

    def test_clear_cache(self):
        """Test clearing provider cache."""
        WalletProviderFactory._provider_cache["test"] = MagicMock()

        WalletProviderFactory.clear_cache()

        assert len(WalletProviderFactory._provider_cache) == 0
