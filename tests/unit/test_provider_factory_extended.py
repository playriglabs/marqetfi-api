"""Extended tests for ProviderFactory."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.exceptions import ExternalServiceError
from app.services.providers.factory import ProviderFactory


class TestProviderFactoryExtended:
    """Extended tests for ProviderFactory class."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear provider caches before each test."""
        ProviderFactory._trading_provider_cache.clear()
        ProviderFactory._price_provider_cache.clear()
        ProviderFactory._settlement_provider_cache.clear()
        ProviderFactory._swap_provider_cache.clear()
        ProviderFactory._auth_provider_cache.clear()
        yield
        # Clean up after test
        ProviderFactory._trading_provider_cache.clear()
        ProviderFactory._price_provider_cache.clear()
        ProviderFactory._settlement_provider_cache.clear()
        ProviderFactory._swap_provider_cache.clear()
        ProviderFactory._auth_provider_cache.clear()

    @pytest.mark.asyncio
    async def test_get_provider_config_lifi(self):
        """Test getting LIFI provider config."""
        with patch("app.services.providers.factory.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.lifi_enabled = True
            mock_settings.LIFI_API_URL = "https://li.xyz/v1"
            mock_settings.LIFI_API_KEY = "test_key"
            mock_settings.lifi_timeout = 30
            mock_settings.lifi_retry_attempts = 3
            mock_settings.lifi_retry_delay = 1.0
            mock_get_settings.return_value = mock_settings

            config = await ProviderFactory._get_provider_config("lifi")

            assert config.enabled is True
            assert config.api_url == "https://li.xyz/v1"
            assert config.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_get_provider_config_auth0(self):
        """Test getting Auth0 provider config."""
        with patch("app.services.providers.factory.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.AUTH0_DOMAIN = "test.auth0.com"
            mock_settings.AUTH0_CLIENT_ID = "test_client_id"
            mock_settings.AUTH0_CLIENT_SECRET = "test_secret"
            mock_settings.AUTH0_AUDIENCE = "test_audience"
            mock_settings.AUTH0_MANAGEMENT_CLIENT_ID = "mgmt_client_id"
            mock_settings.AUTH0_MANAGEMENT_CLIENT_SECRET = "mgmt_secret"
            mock_settings.AUTH0_ALGORITHM = "RS256"
            mock_get_settings.return_value = mock_settings

            config = await ProviderFactory._get_provider_config("auth0")

            assert config.domain == "test.auth0.com"
            assert config.client_id == "test_client_id"
            assert config.enabled is True

    @pytest.mark.asyncio
    async def test_get_provider_config_privy(self):
        """Test getting Privy provider config."""
        with patch("app.services.providers.factory.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.PRIVY_ENABLED = True
            mock_settings.PRIVY_APP_ID = "test_app_id"
            mock_settings.PRIVY_APP_SECRET = "test_secret"
            mock_settings.PRIVY_ENVIRONMENT = "production"
            mock_settings.PRIVY_TIMEOUT = 30
            mock_settings.PRIVY_RETRY_ATTEMPTS = 3
            mock_settings.PRIVY_RETRY_DELAY = 1.0
            mock_get_settings.return_value = mock_settings

            config = await ProviderFactory._get_provider_config("privy")

            assert config.enabled is True
            assert config.app_id == "test_app_id"
            assert config.environment == "production"

    @pytest.mark.asyncio
    async def test_get_provider_config_unknown(self):
        """Test getting unknown provider config."""
        with pytest.raises(ValueError, match="Unknown provider"):
            await ProviderFactory._get_provider_config("unknown_provider")

    @pytest.mark.asyncio
    async def test_get_auth_provider_privy_enabled(self):
        """Test getting auth provider when Privy is enabled."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
            patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_get_config,
        ):
            mock_settings = MagicMock()
            mock_settings.PRIVY_ENABLED = True
            mock_settings.PRIVY_APP_ID = "test_app_id"
            mock_get_settings.return_value = mock_settings

            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock()
            mock_provider_instance.initialize = AsyncMock()
            mock_provider_class.return_value = mock_provider_instance
            mock_registry.get_auth_provider.return_value = mock_provider_class
            mock_get_config.return_value = MagicMock()

            provider = await ProviderFactory.get_auth_provider()

            assert provider == mock_provider_instance
            mock_registry.get_auth_provider.assert_called_once_with("privy")

    @pytest.mark.asyncio
    async def test_get_auth_provider_auth0_enabled(self):
        """Test getting auth provider when Auth0 is enabled."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
            patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_get_config,
        ):
            mock_settings = MagicMock()
            mock_settings.PRIVY_ENABLED = False
            mock_settings.PRIVY_APP_ID = ""
            mock_settings.AUTH0_DOMAIN = "test.auth0.com"
            mock_get_settings.return_value = mock_settings

            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock()
            mock_provider_instance.initialize = AsyncMock()
            mock_provider_class.return_value = mock_provider_instance
            mock_registry.get_auth_provider.return_value = mock_provider_class
            mock_get_config.return_value = MagicMock()

            provider = await ProviderFactory.get_auth_provider()

            assert provider == mock_provider_instance
            mock_registry.get_auth_provider.assert_called_once_with("auth0")

    @pytest.mark.asyncio
    async def test_get_auth_provider_no_provider_configured(self):
        """Test getting auth provider when no provider is configured."""
        with patch("app.services.providers.factory.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.PRIVY_ENABLED = False
            mock_settings.PRIVY_APP_ID = ""
            mock_settings.AUTH0_DOMAIN = ""
            mock_get_settings.return_value = mock_settings

            with pytest.raises(ExternalServiceError, match="No authentication provider configured"):
                await ProviderFactory.get_auth_provider()

    @pytest.mark.asyncio
    async def test_get_auth_provider_cached(self):
        """Test getting cached auth provider."""
        mock_provider = MagicMock()
        ProviderFactory._auth_provider_cache["privy"] = mock_provider

        provider = await ProviderFactory.get_auth_provider(provider_name="privy")

        assert provider == mock_provider

    @pytest.mark.asyncio
    async def test_get_swap_provider_lifi(self):
        """Test getting LIFI swap provider."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
            patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_get_config,
        ):
            mock_settings = MagicMock()
            mock_settings.SWAP_PROVIDER = "lifi"
            mock_get_settings.return_value = mock_settings

            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock()
            mock_provider_instance.initialize = AsyncMock()
            mock_provider_class.return_value = mock_provider_instance
            mock_registry.get_swap_provider.return_value = mock_provider_class
            mock_get_config.return_value = MagicMock()

            provider = await ProviderFactory.get_swap_provider()

            assert provider == mock_provider_instance
            mock_registry.get_swap_provider.assert_called_once_with("lifi")

    @pytest.mark.asyncio
    async def test_get_swap_provider_not_found(self):
        """Test getting swap provider when not found."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
        ):
            mock_settings = MagicMock()
            mock_settings.SWAP_PROVIDER = "unknown"
            mock_get_settings.return_value = mock_settings

            mock_registry.get_swap_provider.return_value = None
            mock_registry.list_swap_providers.return_value = ["lifi"]

            with pytest.raises(ExternalServiceError, match="Swap provider 'unknown' not found"):
                await ProviderFactory.get_swap_provider()

    @pytest.mark.asyncio
    async def test_get_settlement_provider_not_found(self):
        """Test getting settlement provider when not found."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
        ):
            mock_settings = MagicMock()
            mock_settings.SETTLEMENT_PROVIDER = "unknown"
            mock_get_settings.return_value = mock_settings

            mock_registry.get_settlement_provider.return_value = None
            mock_registry.list_settlement_providers.return_value = ["ostium", "lighter"]

            with pytest.raises(
                ExternalServiceError, match="Settlement provider 'unknown' not found"
            ):
                await ProviderFactory.get_settlement_provider()

    @pytest.mark.asyncio
    async def test_get_price_provider_not_found(self):
        """Test getting price provider when not found."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
        ):
            mock_settings = MagicMock()
            mock_settings.PRICE_PROVIDER = "unknown"
            mock_get_settings.return_value = mock_settings

            mock_registry.get_price_provider.return_value = None
            mock_registry.list_price_providers.return_value = ["ostium", "lighter"]

            with pytest.raises(ExternalServiceError, match="Price provider 'unknown' not found"):
                await ProviderFactory.get_price_provider()

    @pytest.mark.asyncio
    async def test_get_trading_provider_not_found(self):
        """Test getting trading provider when not found."""
        with (
            patch("app.services.providers.factory.get_settings") as mock_get_settings,
            patch("app.services.providers.factory.ProviderRegistry") as mock_registry,
        ):
            mock_settings = MagicMock()
            mock_settings.TRADING_PROVIDER = "unknown"
            mock_get_settings.return_value = mock_settings

            mock_registry.get_trading_provider.return_value = None
            mock_registry.list_trading_providers.return_value = ["ostium", "lighter"]

            with pytest.raises(ExternalServiceError, match="Trading provider 'unknown' not found"):
                await ProviderFactory.get_trading_provider()
