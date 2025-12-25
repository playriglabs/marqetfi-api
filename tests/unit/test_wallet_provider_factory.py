"""Test WalletProviderFactory."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.factory import WalletProviderFactory


class TestWalletProviderFactory:
    """Test WalletProviderFactory class."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear provider cache before each test."""
        WalletProviderFactory._provider_cache.clear()
        yield
        WalletProviderFactory._provider_cache.clear()

    @pytest.fixture
    def mock_privy_provider(self):
        """Create mock Privy wallet provider."""
        mock_provider = MagicMock(spec=BaseWalletProvider)
        mock_provider.initialize = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        return mock_provider

    @pytest.fixture
    def mock_dynamic_provider(self):
        """Create mock Dynamic wallet provider."""
        mock_provider = MagicMock(spec=BaseWalletProvider)
        mock_provider.initialize = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        return mock_provider

    @pytest.mark.asyncio
    async def test_get_provider_privy(self, mock_privy_provider):
        """Test getting Privy wallet provider."""
        with patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry:
            from app.services.wallet_providers.privy.provider import PrivyWalletProvider

            mock_registry.get.return_value = PrivyWalletProvider
            mock_registry.list_providers.return_value = ["privy", "dynamic"]

            with patch("app.services.wallet_providers.factory.PrivyWalletProvider") as mock_class:
                mock_class.return_value = mock_privy_provider

                with patch(
                    "app.services.wallet_providers.factory.WalletProviderFactory._get_provider_config"
                ) as mock_config:
                    from app.services.wallet_providers.privy.config import PrivyWalletConfig

                    mock_config.return_value = PrivyWalletConfig(
                        enabled=True,
                        app_id="test",
                        app_secret="test",
                        environment="production",
                        use_embedded_wallets=True,
                        timeout=30,
                        retry_attempts=3,
                        retry_delay=1.0,
                    )

                    provider = await WalletProviderFactory.get_provider("privy")

                    assert provider == mock_privy_provider
                    mock_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_dynamic(self, mock_dynamic_provider):
        """Test getting Dynamic wallet provider."""
        with patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry:
            from app.services.wallet_providers.dynamic.provider import DynamicWalletProvider

            mock_registry.get.return_value = DynamicWalletProvider
            mock_registry.list_providers.return_value = ["privy", "dynamic"]

            with patch("app.services.wallet_providers.factory.DynamicWalletProvider") as mock_class:
                mock_class.return_value = mock_dynamic_provider

                with patch(
                    "app.services.wallet_providers.factory.WalletProviderFactory._get_provider_config"
                ) as mock_config:
                    from app.services.wallet_providers.dynamic.config import DynamicWalletConfig

                    mock_config.return_value = DynamicWalletConfig(
                        enabled=True,
                        api_key="test",
                        api_secret="test",
                        api_url="https://api.dynamic.xyz",
                        environment="production",
                        timeout=30,
                        retry_attempts=3,
                        retry_delay=1.0,
                    )

                    provider = await WalletProviderFactory.get_provider("dynamic")

                    assert provider == mock_dynamic_provider
                    mock_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_cached(self, mock_privy_provider):
        """Test provider caching."""
        with patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry:
            from app.services.wallet_providers.privy.provider import PrivyWalletProvider

            mock_registry.get.return_value = PrivyWalletProvider
            mock_registry.list_providers.return_value = ["privy", "dynamic"]

            with patch("app.services.wallet_providers.factory.PrivyWalletProvider") as mock_class:
                mock_class.return_value = mock_privy_provider

                with patch(
                    "app.services.wallet_providers.factory.WalletProviderFactory._get_provider_config"
                ) as mock_config:
                    from app.services.wallet_providers.privy.config import PrivyWalletConfig

                    mock_config.return_value = PrivyWalletConfig(
                        enabled=True,
                        app_id="test",
                        app_secret="test",
                        environment="production",
                        use_embedded_wallets=True,
                        timeout=30,
                        retry_attempts=3,
                        retry_delay=1.0,
                    )

                    provider1 = await WalletProviderFactory.get_provider("privy")
                    provider2 = await WalletProviderFactory.get_provider("privy")

                    assert provider1 == provider2
                    # Should only be called once due to caching
                    assert mock_class.call_count == 1

    @pytest.mark.asyncio
    async def test_get_provider_invalid(self):
        """Test getting invalid provider."""
        with patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry:
            mock_registry.get.return_value = None
            mock_registry.list_providers.return_value = ["privy", "dynamic"]

            from app.services.wallet_providers.exceptions import WalletProviderUnavailableError

            with pytest.raises(WalletProviderUnavailableError, match="not found"):
                await WalletProviderFactory.get_provider("invalid")

    @pytest.mark.asyncio
    async def test_get_provider_initialization_error(self):
        """Test provider initialization error."""
        with patch("app.services.wallet_providers.factory.WalletProviderRegistry") as mock_registry:
            from app.services.wallet_providers.privy.provider import PrivyWalletProvider

            mock_registry.get.return_value = PrivyWalletProvider
            mock_registry.list_providers.return_value = ["privy", "dynamic"]

            with patch("app.services.wallet_providers.factory.PrivyWalletProvider") as mock_class:
                mock_provider = MagicMock()
                mock_provider.initialize = AsyncMock(side_effect=Exception("Init error"))
                mock_class.return_value = mock_provider

                with patch(
                    "app.services.wallet_providers.factory.WalletProviderFactory._get_provider_config"
                ) as mock_config:
                    from app.services.wallet_providers.privy.config import PrivyWalletConfig

                    mock_config.return_value = PrivyWalletConfig(
                        enabled=True,
                        app_id="test",
                        app_secret="test",
                        environment="production",
                        use_embedded_wallets=True,
                        timeout=30,
                        retry_attempts=3,
                        retry_delay=1.0,
                    )

                    with pytest.raises(Exception, match="Init error"):
                        await WalletProviderFactory.get_provider("privy")
