"""Extended tests for ProviderRouter."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.providers.router import ProviderRouter


class TestProviderRouterExtended:
    """Extended tests for ProviderRouter class."""

    @pytest.fixture
    def router(self):
        """Create ProviderRouter instance."""
        return ProviderRouter()

    def test_configure_asset_category(self, router):
        """Test configuring asset category."""
        router.configure_asset_category("BTC", "crypto", "ostium")

        assert router.get_asset_category("BTC") == "crypto"
        assert router.get_provider_for_asset("BTC") == "ostium"

    def test_configure_asset_category_without_provider(self, router):
        """Test configuring asset category without provider."""
        router.configure_asset_category("ETH", "crypto")

        assert router.get_asset_category("ETH") == "crypto"

    def test_configure_category_provider(self, router):
        """Test configuring category provider."""
        router.configure_category_provider("crypto", "ostium")

        assert router.get_provider_for_category("crypto") == "ostium"

    def test_configure_asset_provider(self, router):
        """Test configuring direct asset provider."""
        router.configure_asset_provider("BTC", "lighter")

        assert router.get_provider_for_asset("BTC") == "lighter"

    def test_get_provider_for_asset_direct(self, router):
        """Test getting provider for asset with direct mapping."""
        router.configure_asset_provider("BTC", "lighter")

        provider = router.get_provider_for_asset("BTC")

        assert provider == "lighter"

    def test_get_provider_for_asset_via_category(self, router):
        """Test getting provider for asset via category."""
        router.configure_asset_category("BTC", "crypto")
        router.configure_category_provider("crypto", "ostium")

        provider = router.get_provider_for_asset("BTC")

        assert provider == "ostium"

    def test_get_provider_for_asset_default(self, router):
        """Test getting provider for asset with default."""
        provider = router.get_provider_for_asset("UNKNOWN", default="ostium")

        assert provider == "ostium"

    @pytest.mark.asyncio
    async def test_get_trading_provider_by_asset(self, router):
        """Test getting trading provider by asset."""
        router.configure_asset_provider("BTC", "ostium")

        with patch(
            "app.services.providers.router.ProviderFactory.get_trading_provider"
        ) as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_trading_provider(asset="BTC")

            assert provider == mock_provider
            mock_get.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_trading_provider_by_asset_type(self, router):
        """Test getting trading provider by asset type."""
        router.configure_category_provider("crypto", "ostium")

        with patch(
            "app.services.providers.router.ProviderFactory.get_trading_provider"
        ) as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_trading_provider(asset_type=1)

            assert provider == mock_provider
            mock_get.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_price_provider_by_asset(self, router):
        """Test getting price provider by asset."""
        router.configure_asset_provider("BTC", "ostium")

        with patch("app.services.providers.router.ProviderFactory.get_price_provider") as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_price_provider(asset="BTC")

            assert provider == mock_provider
            mock_get.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_settlement_provider_by_asset(self, router):
        """Test getting settlement provider by asset."""
        router.configure_asset_provider("BTC", "ostium")

        with patch(
            "app.services.providers.router.ProviderFactory.get_settlement_provider"
        ) as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_settlement_provider(asset="BTC")

            assert provider == mock_provider
            mock_get.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_trading_provider_default(self, router):
        """Test getting trading provider with default."""
        with patch(
            "app.services.providers.router.ProviderFactory.get_trading_provider"
        ) as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_trading_provider()

            assert provider == mock_provider
            mock_get.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_get_price_provider_default(self, router):
        """Test getting price provider with default."""
        with patch("app.services.providers.router.ProviderFactory.get_price_provider") as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_price_provider()

            assert provider == mock_provider
            mock_get.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_get_settlement_provider_default(self, router):
        """Test getting settlement provider with default."""
        with patch(
            "app.services.providers.router.ProviderFactory.get_settlement_provider"
        ) as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            provider = await router.get_settlement_provider()

            assert provider == mock_provider
            mock_get.assert_called_once_with(None)
