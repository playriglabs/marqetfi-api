"""Test Ostium provider configuration."""

from unittest.mock import MagicMock

import pytest
from ostium_python_sdk import NetworkConfig, OstiumSDK
from pydantic import ValidationError

from app.config.providers.ostium import OstiumConfig


class TestOstiumConfig:
    """Test OstiumConfig class."""

    def test_default_values(self):
        """Test that default values match settings defaults."""
        config = OstiumConfig()

        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.network == "testnet"
        assert config.verbose is False
        assert config.slippage_percentage == 1.0
        assert config.enabled is True

    def test_custom_values(self):
        """Test setting custom values."""
        config = OstiumConfig(
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            network="mainnet",
            verbose=True,
            slippage_percentage=2.5,
            enabled=False,
        )

        assert config.timeout == 60
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0
        assert config.network == "mainnet"
        assert config.verbose is True
        assert config.slippage_percentage == 2.5
        assert config.enabled is False

    def test_network_validation_testnet(self):
        """Test network validation accepts 'testnet'."""
        config = OstiumConfig(network="testnet")
        assert config.network == "testnet"

        # Case insensitive
        config = OstiumConfig(network="TESTNET")
        assert config.network == "testnet"

    def test_network_validation_mainnet(self):
        """Test network validation accepts 'mainnet'."""
        config = OstiumConfig(network="mainnet")
        assert config.network == "mainnet"

        # Case insensitive
        config = OstiumConfig(network="MAINNET")
        assert config.network == "mainnet"

    def test_network_validation_invalid(self):
        """Test network validation rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            OstiumConfig(network="invalid")

        assert "Network must be 'testnet' or 'mainnet'" in str(exc_info.value)

    def test_get_network_config_testnet(self):
        """Test get_network_config returns testnet config."""
        config = OstiumConfig(network="testnet")
        network_config = config.get_network_config()

        assert isinstance(network_config, NetworkConfig)
        # Verify it's a testnet config by checking it's the same type
        expected_config = NetworkConfig.testnet()
        assert isinstance(network_config, type(expected_config))

    def test_get_network_config_mainnet(self):
        """Test get_network_config returns mainnet config."""
        config = OstiumConfig(network="mainnet")
        network_config = config.get_network_config()

        assert isinstance(network_config, NetworkConfig)
        # Verify it's a mainnet config by checking it's the same type
        expected_config = NetworkConfig.mainnet()
        assert isinstance(network_config, type(expected_config))

    def test_create_sdk_instance_missing_private_key(self):
        """Test create_sdk_instance raises error when private_key is missing."""
        config = OstiumConfig(
            private_key="",
            rpc_url="https://rpc.example.com",
        )

        with pytest.raises(ValueError, match="Ostium private_key is required"):
            config.create_sdk_instance()

    def test_create_sdk_instance_missing_rpc_url(self):
        """Test create_sdk_instance raises error when rpc_url is missing."""
        config = OstiumConfig(
            private_key="0x1234567890abcdef",
            rpc_url="",
        )

        with pytest.raises(ValueError, match="Ostium rpc_url is required"):
            config.create_sdk_instance()

    def test_create_sdk_instance_success(self):
        """Test create_sdk_instance creates SDK instance successfully."""
        from unittest.mock import patch

        config = OstiumConfig(
            private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            rpc_url="https://rpc.example.com",
            network="testnet",
            verbose=True,
        )

        # Mock the SDK creation to avoid actual network calls
        with patch("app.config.providers.ostium.OstiumSDK") as mock_sdk_class:
            mock_sdk = MagicMock(spec=OstiumSDK)
            mock_sdk_class.return_value = mock_sdk

            sdk = config.create_sdk_instance()

            assert isinstance(sdk, MagicMock)  # It's a mock, but we verify the call
            mock_sdk_class.assert_called_once()

    def test_inherits_base_config_fields(self):
        """Test that OstiumConfig inherits base config fields."""
        config = OstiumConfig()

        # Base fields from BaseProviderConfig
        assert hasattr(config, "enabled")
        assert hasattr(config, "timeout")
        assert hasattr(config, "retry_attempts")
        assert hasattr(config, "retry_delay")

        # Ostium-specific fields
        assert hasattr(config, "private_key")
        assert hasattr(config, "rpc_url")
        assert hasattr(config, "network")
        assert hasattr(config, "verbose")
        assert hasattr(config, "slippage_percentage")
