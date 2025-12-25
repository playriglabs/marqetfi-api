"""Test wallet provider implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.wallet_providers.dynamic.config import DynamicWalletConfig
from app.services.wallet_providers.dynamic.provider import DynamicWalletProvider
from app.services.wallet_providers.privy.config import PrivyWalletConfig
from app.services.wallet_providers.privy.provider import PrivyWalletProvider


class TestPrivyWalletProvider:
    """Test PrivyWalletProvider class."""

    @pytest.fixture
    def privy_config(self):
        """Create Privy config."""
        return PrivyWalletConfig(
            enabled=True,
            app_id="test_app_id",
            app_secret="test_secret",
            environment="production",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
            use_embedded_wallets=True,
        )

    @pytest.fixture
    def privy_provider(self, privy_config):
        """Create PrivyWalletProvider instance."""
        return PrivyWalletProvider(privy_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, privy_provider):
        """Test successful initialization."""
        with patch("app.services.wallet_providers.privy.provider.PrivyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            await privy_provider.initialize()

            assert privy_provider._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_missing_app_id(self, privy_provider):
        """Test initialization with missing app_id."""
        privy_provider.config.app_id = ""

        with pytest.raises(ValueError, match="Privy app_id is required"):
            await privy_provider.initialize()

    @pytest.mark.asyncio
    async def test_health_check_success(self, privy_provider):
        """Test successful health check."""
        mock_client = MagicMock()
        mock_client._get_client = AsyncMock(return_value=MagicMock())
        privy_provider._client = mock_client
        privy_provider._initialized = True

        result = await privy_provider.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, privy_provider):
        """Test successful wallet creation."""
        mock_client = MagicMock()
        mock_client.create_wallet = AsyncMock(return_value={"id": "wallet_123", "address": "0x123"})
        privy_provider._client = mock_client
        privy_provider._initialized = True

        result = await privy_provider.create_wallet("mainnet")

        assert result["wallet_id"] == "wallet_123"
        assert result["address"] == "0x123"

    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, privy_provider):
        """Test successful transaction signing."""
        mock_client = MagicMock()
        mock_client.sign_transaction = AsyncMock(return_value="0xsigned")
        privy_provider._client = mock_client
        privy_provider._initialized = True

        result = await privy_provider.sign_transaction(
            wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100"}
        )

        assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_message_success(self, privy_provider):
        """Test successful message signing."""
        mock_client = MagicMock()
        mock_client.sign_message = AsyncMock(return_value="0xsigned_msg")
        privy_provider._client = mock_client
        privy_provider._initialized = True

        result = await privy_provider.sign_message(wallet_id="wallet_123", message="test message")

        assert result == "0xsigned_msg"


class TestDynamicWalletProvider:
    """Test DynamicWalletProvider class."""

    @pytest.fixture
    def dynamic_config(self):
        """Create Dynamic config."""
        return DynamicWalletConfig(
            enabled=True,
            api_key="test_key",
            api_secret="test_secret",
            api_url="https://api.dynamic.xyz",
            environment="production",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def dynamic_provider(self, dynamic_config):
        """Create DynamicWalletProvider instance."""
        return DynamicWalletProvider(dynamic_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, dynamic_provider):
        """Test successful initialization."""
        with patch(
            "app.services.wallet_providers.dynamic.provider.DynamicClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            await dynamic_provider.initialize()

            assert dynamic_provider._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_missing_api_key(self, dynamic_provider):
        """Test initialization with missing api_key."""
        dynamic_provider.config.api_key = ""

        with pytest.raises(ValueError, match="Dynamic api_key is required"):
            await dynamic_provider.initialize()

    @pytest.mark.asyncio
    async def test_health_check_success(self, dynamic_provider):
        """Test successful health check."""
        mock_client = MagicMock()
        mock_client._request = AsyncMock()
        dynamic_provider._client = mock_client
        dynamic_provider._initialized = True

        result = await dynamic_provider.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, dynamic_provider):
        """Test successful wallet creation."""
        mock_client = MagicMock()
        mock_client.create_wallet = AsyncMock(return_value={"id": "wallet_123", "address": "0x123"})
        dynamic_provider._client = mock_client
        dynamic_provider._initialized = True

        result = await dynamic_provider.create_wallet("mainnet")

        assert result["wallet_id"] == "wallet_123"
        assert result["address"] == "0x123"

    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, dynamic_provider):
        """Test successful transaction signing."""
        mock_client = MagicMock()
        mock_client.sign_transaction = AsyncMock(return_value="0xsigned")
        dynamic_provider._client = mock_client
        dynamic_provider._initialized = True

        result = await dynamic_provider.sign_transaction(
            wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100"}
        )

        assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_message_success(self, dynamic_provider):
        """Test successful message signing."""
        mock_client = MagicMock()
        mock_client.sign_message = AsyncMock(return_value="0xsigned_msg")
        dynamic_provider._client = mock_client
        dynamic_provider._initialized = True

        result = await dynamic_provider.sign_message(wallet_id="wallet_123", message="test message")

        assert result == "0xsigned_msg"
