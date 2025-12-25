"""Test provider base service classes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.lighter import LighterConfig
from app.config.providers.ostium import OstiumConfig
from app.services.providers.exceptions import ServiceUnavailableError
from app.services.providers.lighter.base import LighterService
from app.services.providers.ostium.base import OstiumService


class TestLighterService:
    """Test LighterService class."""

    @pytest.fixture
    def lighter_config(self):
        """Create Lighter config."""
        return LighterConfig(
            enabled=True,
            api_url="https://api.lighter.xyz",
            api_key="test_key",
            private_key="0x123",
            network="mainnet",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def lighter_service(self, lighter_config):
        """Create LighterService instance."""
        return LighterService(lighter_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, lighter_service, lighter_config):
        """Test successful initialization."""
        mock_client = MagicMock()

        with (
            patch.object(lighter_config, "create_api_client", return_value=mock_client),
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_client),
        ):
            await lighter_service.initialize()

            assert lighter_service._initialized is True
            assert lighter_service._client is not None

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, lighter_service):
        """Test initialization when already initialized."""
        lighter_service._initialized = True

        await lighter_service.initialize()

        # Should not re-initialize
        assert lighter_service._initialized is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, lighter_service):
        """Test successful health check."""
        lighter_service._initialized = True
        mock_client = MagicMock()
        lighter_service._client = mock_client

        with (
            patch("app.services.providers.lighter.base.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value={"status": "ok"}),
        ):
            mock_account_api = MagicMock()
            mock_account_api.account = MagicMock()
            mock_lighter.AccountApi = MagicMock(return_value=mock_account_api)

            result = await lighter_service.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, lighter_service):
        """Test health check when not initialized."""
        result = await lighter_service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_sdk_not_installed(self, lighter_service):
        """Test health check when SDK not installed."""
        lighter_service._initialized = True
        lighter_service._client = MagicMock()

        with patch("app.services.providers.lighter.base.lighter", None):
            result = await lighter_service.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_client_property_success(self, lighter_service):
        """Test getting client property."""
        mock_client = MagicMock()
        lighter_service._client = mock_client

        client = lighter_service.client

        assert client is mock_client

    @pytest.mark.asyncio
    async def test_client_property_not_initialized(self, lighter_service):
        """Test getting client property when not initialized."""
        with pytest.raises(ServiceUnavailableError):
            _ = lighter_service.client

    @pytest.mark.asyncio
    async def test_close_success(self, lighter_service):
        """Test closing client."""
        mock_client = MagicMock()
        mock_client.close = MagicMock()
        lighter_service._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock):
            await lighter_service.close()

            assert lighter_service._client is None


class TestOstiumService:
    """Test OstiumService class."""

    @pytest.fixture
    def ostium_config(self):
        """Create Ostium config."""
        return OstiumConfig(
            enabled=True,
            private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            rpc_url="https://rpc.example.com",
            network="testnet",
            slippage_percentage=1.0,
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def ostium_service(self, ostium_config):
        """Create OstiumService instance."""
        return OstiumService(ostium_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, ostium_service, ostium_config):
        """Test successful initialization."""
        mock_sdk = MagicMock()
        mock_sdk.web3 = None
        mock_sdk.w3 = None

        with (
            patch.object(ostium_config, "create_sdk_instance", return_value=mock_sdk),
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_sdk),
            patch("app.services.providers.ostium.base.Web3") as mock_web3,
        ):
            mock_web3_instance = MagicMock()
            mock_web3.return_value = mock_web3_instance

            await ostium_service.initialize()

            assert ostium_service._initialized is True
            assert ostium_service._sdk is not None

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, ostium_service):
        """Test initialization when already initialized."""
        ostium_service._initialized = True

        await ostium_service.initialize()

        # Should not re-initialize
        assert ostium_service._initialized is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, ostium_service):
        """Test successful health check."""
        ostium_service._initialized = True
        mock_sdk = MagicMock()
        mock_sdk.subgraph = MagicMock()
        mock_sdk.subgraph.get_pairs = MagicMock(return_value=[])
        ostium_service._sdk = mock_sdk

        with patch.object(
            ostium_service, "_execute_with_retry", new_callable=AsyncMock, return_value=[]
        ):
            result = await ostium_service.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, ostium_service):
        """Test health check when not initialized."""
        result = await ostium_service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_sdk_property_success(self, ostium_service):
        """Test getting SDK property."""
        mock_sdk = MagicMock()
        ostium_service._sdk = mock_sdk

        sdk = ostium_service.sdk

        assert sdk is mock_sdk

    @pytest.mark.asyncio
    async def test_sdk_property_not_initialized(self, ostium_service):
        """Test getting SDK property when not initialized."""
        with pytest.raises(ServiceUnavailableError):
            _ = ostium_service.sdk

    @pytest.mark.asyncio
    async def test_get_web3_from_sdk(self, ostium_service):
        """Test getting web3 from SDK."""
        mock_sdk = MagicMock()
        mock_web3 = MagicMock()
        mock_sdk.web3 = mock_web3
        ostium_service._sdk = mock_sdk

        web3 = ostium_service.get_web3()

        assert web3 is mock_web3

    @pytest.mark.asyncio
    async def test_get_web3_create_new(self, ostium_service, ostium_config):
        """Test creating new web3 instance."""
        ostium_service._web3 = None
        ostium_service._sdk = None

        with patch("app.services.providers.ostium.base.Web3") as mock_web3:
            mock_web3_instance = MagicMock()
            mock_web3.return_value = mock_web3_instance

            web3 = ostium_service.get_web3()

            assert web3 is not None

    @pytest.mark.asyncio
    async def test_get_web3_no_rpc_url(self, ostium_service):
        """Test getting web3 when RPC URL not configured."""
        ostium_service._web3 = None
        ostium_service._sdk = None
        ostium_service.config.rpc_url = None

        with pytest.raises(ServiceUnavailableError):
            ostium_service.get_web3()

    @pytest.mark.asyncio
    async def test_wallet_signer_property(self, ostium_service):
        """Test getting wallet signer property."""
        mock_signer = MagicMock()
        ostium_service._wallet_signer = mock_signer

        signer = ostium_service.wallet_signer

        assert signer is mock_signer
