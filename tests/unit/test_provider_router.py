"""Test ProviderRouter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.base import (
    BasePriceProvider,
    BaseSettlementProvider,
    BaseTradingProvider,
)
from app.services.providers.router import ProviderRouter, get_provider_router


class TestProviderRouter:
    """Test ProviderRouter class."""

    @pytest.fixture
    def router(self):
        """Create ProviderRouter instance."""
        return ProviderRouter()

    @pytest.fixture
    def mock_trading_provider(self):
        """Create mock trading provider."""
        return MagicMock(spec=BaseTradingProvider)

    @pytest.fixture
    def mock_price_provider(self):
        """Create mock price provider."""
        return MagicMock(spec=BasePriceProvider)

    @pytest.fixture
    def mock_settlement_provider(self):
        """Create mock settlement provider."""
        return MagicMock(spec=BaseSettlementProvider)

    def test_configure_asset_category(self, router):
        """Test configuring asset category."""
        router.configure_asset_category("BTC", "crypto", "lighter")
        assert router._asset_category_map["BTC"] == "crypto"
        assert router._asset_provider_map["BTC"] == "lighter"

    def test_configure_category_provider(self, router):
        """Test configuring category provider."""
        router.configure_category_provider("crypto", "lighter")
        assert router._category_provider_map["crypto"] == "lighter"

    def test_configure_asset_provider(self, router):
        """Test configuring asset provider."""
        router.configure_asset_provider("BTC", "lighter")
        assert router._asset_provider_map["BTC"] == "lighter"

    def test_get_asset_category_direct_mapping(self, router):
        """Test getting asset category from direct mapping."""
        router.configure_asset_provider("BTC", "lighter")
        category = router.get_asset_category("BTC")
        assert category == "crypto"

    def test_get_asset_category_from_map(self, router):
        """Test getting asset category from category map."""
        router.configure_asset_category("EUR", "forex")
        category = router.get_asset_category("EUR")
        assert category == "forex"

    def test_get_asset_category_crypto_inference(self, router):
        """Test inferring crypto category from common assets."""
        category = router.get_asset_category("BTC")
        assert category == "crypto"

        category = router.get_asset_category("ETH")
        assert category == "crypto"

    def test_get_asset_category_default_tradfi(self, router):
        """Test default tradfi category for unknown assets."""
        category = router.get_asset_category("UNKNOWN")
        assert category == "tradfi"

    def test_get_provider_for_asset_direct(self, router):
        """Test getting provider from direct mapping."""
        router.configure_asset_provider("BTC", "lighter")
        provider = router.get_provider_for_asset("BTC")
        assert provider == "lighter"

    def test_get_provider_for_asset_category(self, router):
        """Test getting provider from category."""
        router.configure_category_provider("crypto", "lighter")
        router.configure_asset_category("ETH", "crypto")
        provider = router.get_provider_for_asset("ETH")
        assert provider == "lighter"

    def test_get_provider_for_asset_default(self, router):
        """Test default provider fallback."""
        provider = router.get_provider_for_asset("UNKNOWN")
        assert provider == "ostium"

    def test_get_provider_for_asset_type_crypto(self, router):
        """Test getting provider for crypto asset type."""
        provider = router.get_provider_for_asset_type(0)  # BTC
        assert provider == "lighter"

        provider = router.get_provider_for_asset_type(1)  # ETH
        assert provider == "lighter"

    def test_get_provider_for_asset_type_tradfi(self, router):
        """Test getting provider for tradfi asset type."""
        provider = router.get_provider_for_asset_type(2)  # Non-crypto
        assert provider == "ostium"

    @pytest.mark.asyncio
    async def test_get_trading_provider_by_asset(self, router, mock_trading_provider):
        """Test getting trading provider by asset."""
        router.configure_asset_provider("BTC", "lighter")

        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_trading_provider = AsyncMock(return_value=mock_trading_provider)

            provider = await router.get_trading_provider(asset="BTC")

            assert provider == mock_trading_provider
            mock_factory.get_trading_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_trading_provider_by_asset_type(self, router, mock_trading_provider):
        """Test getting trading provider by asset type."""
        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_trading_provider = AsyncMock(return_value=mock_trading_provider)

            provider = await router.get_trading_provider(asset_type=0)

            assert provider == mock_trading_provider
            mock_factory.get_trading_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_trading_provider_default(self, router, mock_trading_provider):
        """Test getting default trading provider."""
        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_trading_provider = AsyncMock(return_value=mock_trading_provider)

            with patch("app.services.providers.router.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.TRADING_PROVIDER = "ostium"
                mock_get_settings.return_value = mock_settings

                provider = await router.get_trading_provider()

                assert provider == mock_trading_provider
                mock_factory.get_trading_provider.assert_called_once_with("ostium")

    @pytest.mark.asyncio
    async def test_get_price_provider(self, router, mock_price_provider):
        """Test getting price provider."""
        router.configure_asset_provider("BTC", "lighter")

        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_price_provider = AsyncMock(return_value=mock_price_provider)

            provider = await router.get_price_provider("BTC")

            assert provider == mock_price_provider
            mock_factory.get_price_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_settlement_provider_by_asset(self, router, mock_settlement_provider):
        """Test getting settlement provider by asset."""
        router.configure_asset_provider("BTC", "lighter")

        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_settlement_provider = AsyncMock(return_value=mock_settlement_provider)

            provider = await router.get_settlement_provider(asset="BTC")

            assert provider == mock_settlement_provider
            mock_factory.get_settlement_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_settlement_provider_by_asset_type(self, router, mock_settlement_provider):
        """Test getting settlement provider by asset type."""
        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_settlement_provider = AsyncMock(return_value=mock_settlement_provider)

            provider = await router.get_settlement_provider(asset_type=0)

            assert provider == mock_settlement_provider
            mock_factory.get_settlement_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_settlement_provider_default(self, router, mock_settlement_provider):
        """Test getting default settlement provider."""
        with patch("app.services.providers.router.ProviderFactory") as mock_factory:
            mock_factory.get_settlement_provider = AsyncMock(return_value=mock_settlement_provider)

            with patch("app.services.providers.router.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.SETTLEMENT_PROVIDER = "ostium"
                mock_get_settings.return_value = mock_settings

                provider = await router.get_settlement_provider()

                assert provider == mock_settlement_provider
                mock_factory.get_settlement_provider.assert_called_once_with("ostium")

    def test_get_provider_router_singleton(self):
        """Test get_provider_router returns singleton."""
        router1 = get_provider_router()
        router2 = get_provider_router()
        assert router1 is router2

    def test_get_provider_router_default_config(self):
        """Test default router configuration."""
        router = get_provider_router()
        assert router._category_provider_map["crypto"] == "lighter"
        assert router._category_provider_map["forex"] == "ostium"
        assert router.get_asset_category("BTC") == "crypto"
