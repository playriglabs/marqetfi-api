"""Test ProviderFactory."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.exceptions import ExternalServiceError
from app.services.providers.factory import ProviderFactory


class TestProviderFactory:
    """Test ProviderFactory class."""

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

    @pytest.fixture
    def mock_trading_provider_class(self):
        """Create mock trading provider class."""
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initialize = AsyncMock()
        mock_class.return_value = mock_instance
        return mock_class, mock_instance

    @pytest.fixture
    def mock_price_provider_class(self):
        """Create mock price provider class."""
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initialize = AsyncMock()
        mock_class.return_value = mock_instance
        return mock_class, mock_instance

    @pytest.fixture
    def mock_settlement_provider_class(self):
        """Create mock settlement provider class."""
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initialize = AsyncMock()
        mock_class.return_value = mock_instance
        return mock_class, mock_instance

    @pytest.fixture
    def mock_swap_provider_class(self):
        """Create mock swap provider class."""
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initialize = AsyncMock()
        mock_class.return_value = mock_instance
        return mock_class, mock_instance

    @pytest.fixture
    def mock_auth_provider_class(self):
        """Create mock auth provider class."""
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initialize = AsyncMock()
        mock_class.return_value = mock_instance
        return mock_class, mock_instance

    @pytest.mark.asyncio
    async def test_get_trading_provider_success(self, mock_trading_provider_class):
        """Test getting trading provider successfully."""
        mock_class, mock_instance = mock_trading_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_trading_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                mock_registry.return_value = mock_class
                mock_config.return_value = MagicMock()

                result = await ProviderFactory.get_trading_provider("ostium")

                assert result == mock_instance
                mock_instance.initialize.assert_called_once()
                assert "ostium" in ProviderFactory._trading_provider_cache

    @pytest.mark.asyncio
    async def test_get_trading_provider_default(self, mock_trading_provider_class):
        """Test getting trading provider with default name."""
        mock_class, mock_instance = mock_trading_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_trading_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                with patch("app.config.get_settings") as mock_settings:
                    mock_registry.return_value = mock_class
                    mock_config.return_value = MagicMock()
                    mock_settings.return_value = MagicMock(TRADING_PROVIDER="ostium")

                    result = await ProviderFactory.get_trading_provider()

                    assert result == mock_instance
                    mock_registry.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_trading_provider_not_found(self):
        """Test getting non-existent trading provider."""
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_trading_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderRegistry.list_trading_providers"
            ) as mock_list:
                mock_registry.return_value = None
                mock_list.return_value = ["ostium", "lighter"]

                with pytest.raises(ExternalServiceError) as exc_info:
                    await ProviderFactory.get_trading_provider("invalid")

                assert "Trading provider 'invalid' not found" in str(exc_info.value)
                assert "Available: ['ostium', 'lighter']" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_trading_provider_cached(self, mock_trading_provider_class):
        """Test getting cached trading provider."""
        mock_class, mock_instance = mock_trading_provider_class
        ProviderFactory._trading_provider_cache["ostium"] = mock_instance

        result = await ProviderFactory.get_trading_provider("ostium")

        assert result == mock_instance
        # Should not call registry or config again
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_trading_provider"
        ) as mock_registry:
            mock_registry.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_price_provider_success(self, mock_price_provider_class):
        """Test getting price provider successfully."""
        mock_class, mock_instance = mock_price_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_price_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                mock_registry.return_value = mock_class
                mock_config.return_value = MagicMock()

                result = await ProviderFactory.get_price_provider("ostium")

                assert result == mock_instance
                mock_instance.initialize.assert_called_once()
                assert "ostium" in ProviderFactory._price_provider_cache

    @pytest.mark.asyncio
    async def test_get_price_provider_not_found(self):
        """Test getting non-existent price provider."""
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_price_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderRegistry.list_price_providers"
            ) as mock_list:
                mock_registry.return_value = None
                mock_list.return_value = ["ostium", "lighter"]

                with pytest.raises(ExternalServiceError) as exc_info:
                    await ProviderFactory.get_price_provider("invalid")

                assert "Price provider 'invalid' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_settlement_provider_success(self, mock_settlement_provider_class):
        """Test getting settlement provider successfully."""
        mock_class, mock_instance = mock_settlement_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_settlement_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                mock_registry.return_value = mock_class
                mock_config.return_value = MagicMock()

                result = await ProviderFactory.get_settlement_provider("ostium")

                assert result == mock_instance
                mock_instance.initialize.assert_called_once()
                assert "ostium" in ProviderFactory._settlement_provider_cache

    @pytest.mark.asyncio
    async def test_get_settlement_provider_not_found(self):
        """Test getting non-existent settlement provider."""
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_settlement_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderRegistry.list_settlement_providers"
            ) as mock_list:
                mock_registry.return_value = None
                mock_list.return_value = ["ostium"]

                with pytest.raises(ExternalServiceError) as exc_info:
                    await ProviderFactory.get_settlement_provider("invalid")

                assert "Settlement provider 'invalid' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_swap_provider_success(self, mock_swap_provider_class):
        """Test getting swap provider successfully."""
        mock_class, mock_instance = mock_swap_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_swap_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                mock_registry.return_value = mock_class
                mock_config.return_value = MagicMock()

                result = await ProviderFactory.get_swap_provider("lifi")

                assert result == mock_instance
                mock_instance.initialize.assert_called_once()
                assert "lifi" in ProviderFactory._swap_provider_cache

    @pytest.mark.asyncio
    async def test_get_swap_provider_not_found(self):
        """Test getting non-existent swap provider."""
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_swap_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderRegistry.list_swap_providers"
            ) as mock_list:
                mock_registry.return_value = None
                mock_list.return_value = ["lifi"]

                with pytest.raises(ExternalServiceError) as exc_info:
                    await ProviderFactory.get_swap_provider("invalid")

                assert "Swap provider 'invalid' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_auth_provider_success(self, mock_auth_provider_class):
        """Test getting auth provider successfully."""
        mock_class, mock_instance = mock_auth_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_auth_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                mock_registry.return_value = mock_class
                mock_config.return_value = MagicMock()

                result = await ProviderFactory.get_auth_provider("auth0")

                assert result == mock_instance
                mock_instance.initialize.assert_called_once()
                assert "auth0" in ProviderFactory._auth_provider_cache

    @pytest.mark.asyncio
    async def test_get_auth_provider_default_privy(self, mock_auth_provider_class):
        """Test getting auth provider with default (privy)."""
        mock_class, mock_instance = mock_auth_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_auth_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                with patch("app.config.get_settings") as mock_settings:
                    mock_registry.return_value = mock_class
                    mock_config.return_value = MagicMock()
                    mock_settings.return_value = MagicMock(
                        PRIVY_ENABLED=True, PRIVY_APP_ID="test_id"
                    )

                    result = await ProviderFactory.get_auth_provider()

                    assert result == mock_instance
                    mock_registry.assert_called_once_with("privy")

    @pytest.mark.asyncio
    async def test_get_auth_provider_default_auth0(self, mock_auth_provider_class):
        """Test getting auth provider with default (auth0 when privy not enabled)."""
        mock_class, mock_instance = mock_auth_provider_class

        with patch(
            "app.services.providers.factory.ProviderRegistry.get_auth_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderFactory._get_provider_config"
            ) as mock_config:
                with patch("app.config.get_settings") as mock_settings:
                    mock_registry.return_value = mock_class
                    mock_config.return_value = MagicMock()
                    mock_settings.return_value = MagicMock(
                        PRIVY_ENABLED=False, PRIVY_APP_ID="", AUTH0_DOMAIN="test.domain"
                    )

                    result = await ProviderFactory.get_auth_provider()

                    assert result == mock_instance
                    mock_registry.assert_called_once_with("auth0")

    @pytest.mark.asyncio
    async def test_get_auth_provider_no_config(self):
        """Test getting auth provider when none configured."""
        with patch("app.services.providers.factory.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                PRIVY_ENABLED=False, PRIVY_APP_ID="", AUTH0_DOMAIN=""
            )

            with pytest.raises(ExternalServiceError) as exc_info:
                await ProviderFactory.get_auth_provider()

            assert "No authentication provider configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_auth_provider_not_found(self):
        """Test getting non-existent auth provider."""
        with patch(
            "app.services.providers.factory.ProviderRegistry.get_auth_provider"
        ) as mock_registry:
            with patch(
                "app.services.providers.factory.ProviderRegistry.list_auth_providers"
            ) as mock_list:
                mock_registry.return_value = None
                mock_list.return_value = ["auth0", "privy"]

                with pytest.raises(ExternalServiceError) as exc_info:
                    await ProviderFactory.get_auth_provider("invalid")

                assert "Authentication provider 'invalid' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_provider_config_ostium(self):
        """Test getting Ostium provider config."""
        # Mock database path to fail and fall back to environment
        with patch("app.services.providers.factory.OstiumAdminService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_active_config = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            # Make session creation fail
            with patch("app.core.database.get_session_maker", side_effect=Exception("No DB")):
                with patch("app.config.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(
                        ostium_private_key="0x123",
                        ostium_rpc_url="https://rpc.example.com",
                        ostium_network="testnet",
                        ostium_enabled=True,
                        ostium_verbose=False,
                        ostium_slippage_percentage=1.0,
                        ostium_timeout=30,
                        ostium_retry_attempts=3,
                        ostium_retry_delay=1.0,
                        WALLET_PROVIDER="none",
                        OSTIUM_USE_WALLET_PROVIDER=False,
                        OSTIUM_WALLET_PROVIDER_ID=None,
                        OSTIUM_FALLBACK_TO_PRIVATE_KEY=True,
                    )

                    config = await ProviderFactory._get_provider_config("ostium")

                    assert config is not None
                    assert hasattr(config, "private_key")
                    assert hasattr(config, "rpc_url")
                    assert hasattr(config, "network")

    @pytest.mark.asyncio
    async def test_get_provider_config_lighter(self):
        """Test getting Lighter provider config."""
        # Mock database path to fail and fall back to environment
        with patch("app.services.providers.factory.ConfigurationService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_provider_config = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            # Make session creation fail
            with patch("app.core.database.get_session_maker", side_effect=Exception("No DB")):
                with patch("app.config.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(
                        lighter_enabled=True,
                        lighter_api_url="https://api.lighter.xyz",
                        lighter_api_key="test_key",
                        lighter_private_key="0x123",
                        lighter_network="mainnet",
                        lighter_timeout=30,
                        lighter_retry_attempts=3,
                        lighter_retry_delay=1.0,
                    )

                    config = await ProviderFactory._get_provider_config("lighter")

                    assert config is not None
                    assert hasattr(config, "api_url")
                    assert hasattr(config, "network")

    @pytest.mark.asyncio
    async def test_get_provider_config_lifi(self):
        """Test getting LI-FI provider config."""
        # Mock database path to fail and fall back to environment
        with patch("app.services.providers.factory.ConfigurationService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_provider_config = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            # Make session creation fail
            with patch("app.core.database.get_session_maker", side_effect=Exception("No DB")):
                with patch("app.config.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(
                        lifi_enabled=True,
                        LIFI_API_URL="https://li.xyz/v1",
                        LIFI_API_KEY=None,
                        lifi_timeout=30,
                        lifi_retry_attempts=3,
                        lifi_retry_delay=1.0,
                    )

                    config = await ProviderFactory._get_provider_config("lifi")

                    assert config is not None
                    assert hasattr(config, "api_url")

    @pytest.mark.asyncio
    async def test_get_provider_config_auth0(self):
        """Test getting Auth0 provider config."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AUTH0_DOMAIN="test.auth0.com",
                AUTH0_CLIENT_ID="client_id",
                AUTH0_CLIENT_SECRET="secret",
                AUTH0_AUDIENCE="audience",
                AUTH0_MANAGEMENT_CLIENT_ID="mgmt_id",
                AUTH0_MANAGEMENT_CLIENT_SECRET="mgmt_secret",
                AUTH0_ALGORITHM="RS256",
            )

            config = await ProviderFactory._get_provider_config("auth0")

            assert config is not None
            assert hasattr(config, "domain")
            assert hasattr(config, "client_id")

    @pytest.mark.asyncio
    async def test_get_provider_config_privy(self):
        """Test getting Privy provider config."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                PRIVY_ENABLED=True,
                PRIVY_APP_ID="app_id",
                PRIVY_APP_SECRET="secret",
                PRIVY_ENVIRONMENT="production",
                PRIVY_TIMEOUT=30,
                PRIVY_RETRY_ATTEMPTS=3,
                PRIVY_RETRY_DELAY=1.0,
            )

            config = await ProviderFactory._get_provider_config("privy")

            assert config is not None
            assert hasattr(config, "app_id")
            assert hasattr(config, "app_secret")

    @pytest.mark.asyncio
    async def test_get_provider_config_unknown(self):
        """Test getting unknown provider config."""
        with pytest.raises(ValueError) as exc_info:
            await ProviderFactory._get_provider_config("unknown_provider")

        assert "Unknown provider: unknown_provider" in str(exc_info.value)
