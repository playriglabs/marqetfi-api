"""Test WalletProviderRegistry."""

import pytest

from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.registry import WalletProviderRegistry


class TestWalletProviderRegistry:
    """Test WalletProviderRegistry class."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        WalletProviderRegistry._providers.clear()
        yield
        # Clean up after test
        WalletProviderRegistry._providers.clear()

    def test_register_provider(self):
        """Test registering a wallet provider."""

        class MockWalletProvider(BaseWalletProvider):
            pass

        WalletProviderRegistry.register("test", MockWalletProvider)

        assert WalletProviderRegistry.get("test") == MockWalletProvider
        assert WalletProviderRegistry.has("test") is True

    def test_get_provider_not_found(self):
        """Test getting provider that doesn't exist."""
        assert WalletProviderRegistry.get("nonexistent") is None

    def test_has_provider_false(self):
        """Test checking for provider that doesn't exist."""
        assert WalletProviderRegistry.has("nonexistent") is False

    def test_list_providers_empty(self):
        """Test listing providers when empty."""
        assert WalletProviderRegistry.list_providers() == []

    def test_list_providers(self):
        """Test listing providers."""

        class MockProvider1(BaseWalletProvider):
            pass

        class MockProvider2(BaseWalletProvider):
            pass

        WalletProviderRegistry.register("provider1", MockProvider1)
        WalletProviderRegistry.register("provider2", MockProvider2)

        providers = WalletProviderRegistry.list_providers()

        assert "provider1" in providers
        assert "provider2" in providers
        assert len(providers) == 2
