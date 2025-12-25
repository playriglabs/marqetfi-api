"""Test ProviderRegistry."""

import pytest

from app.services.providers.base import (
    BaseAuthProvider,
    BasePriceProvider,
    BaseSettlementProvider,
    BaseSwapProvider,
    BaseTradingProvider,
)
from app.services.providers.registry import ProviderRegistry


class TestProviderRegistry:
    """Test ProviderRegistry class."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        ProviderRegistry._trading_providers.clear()
        ProviderRegistry._price_providers.clear()
        ProviderRegistry._settlement_providers.clear()
        ProviderRegistry._swap_providers.clear()
        ProviderRegistry._auth_providers.clear()
        yield
        # Clean up after test
        ProviderRegistry._trading_providers.clear()
        ProviderRegistry._price_providers.clear()
        ProviderRegistry._settlement_providers.clear()
        ProviderRegistry._swap_providers.clear()
        ProviderRegistry._auth_providers.clear()

    def test_register_trading_provider(self):
        """Test registering a trading provider."""

        class MockTradingProvider(BaseTradingProvider):
            pass

        ProviderRegistry.register_trading_provider("test", MockTradingProvider)

        assert ProviderRegistry.get_trading_provider("test") == MockTradingProvider
        assert "test" in ProviderRegistry.list_trading_providers()

    def test_register_price_provider(self):
        """Test registering a price provider."""

        class MockPriceProvider(BasePriceProvider):
            pass

        ProviderRegistry.register_price_provider("test", MockPriceProvider)

        assert ProviderRegistry.get_price_provider("test") == MockPriceProvider
        assert "test" in ProviderRegistry.list_price_providers()

    def test_register_settlement_provider(self):
        """Test registering a settlement provider."""

        class MockSettlementProvider(BaseSettlementProvider):
            pass

        ProviderRegistry.register_settlement_provider("test", MockSettlementProvider)

        assert ProviderRegistry.get_settlement_provider("test") == MockSettlementProvider
        assert "test" in ProviderRegistry.list_settlement_providers()

    def test_register_swap_provider(self):
        """Test registering a swap provider."""

        class MockSwapProvider(BaseSwapProvider):
            pass

        ProviderRegistry.register_swap_provider("test", MockSwapProvider)

        assert ProviderRegistry.get_swap_provider("test") == MockSwapProvider
        assert "test" in ProviderRegistry.list_swap_providers()

    def test_register_auth_provider(self):
        """Test registering an auth provider."""

        class MockAuthProvider(BaseAuthProvider):
            pass

        ProviderRegistry.register_auth_provider("test", MockAuthProvider)

        assert ProviderRegistry.get_auth_provider("test") == MockAuthProvider
        assert "test" in ProviderRegistry.list_auth_providers()

    def test_get_trading_provider_not_found(self):
        """Test getting trading provider that doesn't exist."""
        assert ProviderRegistry.get_trading_provider("nonexistent") is None

    def test_get_price_provider_not_found(self):
        """Test getting price provider that doesn't exist."""
        assert ProviderRegistry.get_price_provider("nonexistent") is None

    def test_get_settlement_provider_not_found(self):
        """Test getting settlement provider that doesn't exist."""
        assert ProviderRegistry.get_settlement_provider("nonexistent") is None

    def test_get_swap_provider_not_found(self):
        """Test getting swap provider that doesn't exist."""
        assert ProviderRegistry.get_swap_provider("nonexistent") is None

    def test_get_auth_provider_not_found(self):
        """Test getting auth provider that doesn't exist."""
        assert ProviderRegistry.get_auth_provider("nonexistent") is None

    def test_list_trading_providers_empty(self):
        """Test listing trading providers when empty."""
        assert ProviderRegistry.list_trading_providers() == []

    def test_list_price_providers_empty(self):
        """Test listing price providers when empty."""
        assert ProviderRegistry.list_price_providers() == []

    def test_list_settlement_providers_empty(self):
        """Test listing settlement providers when empty."""
        assert ProviderRegistry.list_settlement_providers() == []

    def test_list_swap_providers_empty(self):
        """Test listing swap providers when empty."""
        assert ProviderRegistry.list_swap_providers() == []

    def test_list_auth_providers_empty(self):
        """Test listing auth providers when empty."""
        assert ProviderRegistry.list_auth_providers() == []
