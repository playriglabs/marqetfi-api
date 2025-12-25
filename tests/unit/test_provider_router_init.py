"""Test ProviderRouter initialization."""

from unittest.mock import MagicMock, patch

from app.services.providers.router import (
    ProviderRouter,
    _initialize_default_routing,
    get_provider_router,
)


class TestProviderRouterInitialization:
    """Test ProviderRouter initialization and default routing."""

    def test_initialize_default_routing(self):
        """Test default routing initialization."""
        router = ProviderRouter()
        _initialize_default_routing(router)

        assert router._category_provider_map["crypto"] == "lighter"
        assert router._category_provider_map["forex"] == "ostium"
        assert router._category_provider_map["indices"] == "ostium"
        assert router._category_provider_map["commodities"] == "ostium"
        assert router._category_provider_map["tradfi"] == "ostium"

        # Check crypto assets are configured
        assert router.get_asset_category("BTC") == "crypto"
        assert router.get_asset_category("ETH") == "crypto"
        assert router.get_asset_category("SOL") == "crypto"

    def test_initialize_default_routing_with_custom_dict(self):
        """Test default routing with custom ASSET_ROUTING dict."""
        router = ProviderRouter()

        with patch("app.services.providers.router.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.ASSET_ROUTING = {"CUSTOM": "lighter", "OTHER": "ostium"}
            mock_get_settings.return_value = mock_settings

            _initialize_default_routing(router)

            assert router.get_provider_for_asset("CUSTOM") == "lighter"
            assert router.get_provider_for_asset("OTHER") == "ostium"

    def test_initialize_default_routing_with_custom_json_string(self):
        """Test default routing with custom ASSET_ROUTING JSON string."""
        router = ProviderRouter()

        with patch("app.services.providers.router.get_settings") as mock_get_settings:
            import json

            mock_settings = MagicMock()
            mock_settings.ASSET_ROUTING = json.dumps({"CUSTOM": "lighter", "OTHER": "ostium"})
            mock_get_settings.return_value = mock_settings

            _initialize_default_routing(router)

            assert router.get_provider_for_asset("CUSTOM") == "lighter"
            assert router.get_provider_for_asset("OTHER") == "ostium"

    def test_initialize_default_routing_with_invalid_json(self):
        """Test default routing with invalid JSON string."""
        router = ProviderRouter()

        with patch("app.services.providers.router.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.ASSET_ROUTING = "invalid json"
            mock_get_settings.return_value = mock_settings

            # Should not raise exception
            _initialize_default_routing(router)

            # Default routing should still be applied
            assert router._category_provider_map["crypto"] == "lighter"

    def test_get_provider_router_singleton(self):
        """Test get_provider_router returns singleton."""
        # Reset global router
        import app.services.providers.router

        app.services.providers.router._provider_router = None

        router1 = get_provider_router()
        router2 = get_provider_router()

        assert router1 is router2

    def test_get_provider_router_initializes_defaults(self):
        """Test get_provider_router initializes default routing."""
        # Reset global router
        import app.services.providers.router

        app.services.providers.router._provider_router = None

        router = get_provider_router()

        assert router._category_provider_map["crypto"] == "lighter"
        assert router.get_asset_category("BTC") == "crypto"

    def test_get_provider_for_asset_with_default(self):
        """Test get_provider_for_asset with default parameter."""
        router = ProviderRouter()

        provider = router.get_provider_for_asset("UNKNOWN", default="custom")

        assert provider == "custom"

    def test_get_asset_category_ostium_provider(self):
        """Test get_asset_category with Ostium provider."""
        router = ProviderRouter()
        router.configure_asset_provider("EURUSD", "ostium")

        category = router.get_asset_category("EURUSD")

        assert category == "tradfi"

    def test_get_asset_category_lighter_provider(self):
        """Test get_asset_category with Lighter provider."""
        router = ProviderRouter()
        router.configure_asset_provider("BTC", "lighter")

        category = router.get_asset_category("BTC")

        assert category == "crypto"
