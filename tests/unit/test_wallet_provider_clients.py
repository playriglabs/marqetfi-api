"""Test wallet provider client implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.wallet_providers.dynamic.client import DynamicClient
from app.services.wallet_providers.dynamic.config import DynamicWalletConfig
from app.services.wallet_providers.privy.client import PrivyClient
from app.services.wallet_providers.privy.config import PrivyWalletConfig


class TestDynamicClient:
    """Test DynamicClient class."""

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
    def dynamic_client(self, dynamic_config):
        """Create DynamicClient instance."""
        return DynamicClient(dynamic_config)

    @pytest.mark.asyncio
    async def test_get_client_success(self, dynamic_client):
        """Test successful client creation."""
        client = await dynamic_client._get_client()

        assert client is not None
        assert isinstance(client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_request_success(self, dynamic_client):
        """Test successful HTTP request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "wallet_123", "address": "0x123"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(dynamic_client, "_get_client") as mock_get_client:
            mock_http_client = MagicMock()
            mock_http_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http_client

            result = await dynamic_client._request("GET", "/v1/wallets")

            assert result["id"] == "wallet_123"

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, dynamic_client):
        """Test successful wallet creation."""
        with patch.object(dynamic_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "wallet_123", "address": "0x123"}

            result = await dynamic_client.create_wallet("mainnet")

            assert result["id"] == "wallet_123"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, dynamic_client):
        """Test successful transaction signing."""
        with patch.object(dynamic_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"transaction_hash": "0xsigned"}

            result = await dynamic_client.sign_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100"}
            )

            assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_message_success(self, dynamic_client):
        """Test successful message signing."""
        with patch.object(dynamic_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"signature": "0xsigned_msg"}

            result = await dynamic_client.sign_message(
                wallet_id="wallet_123", message="test message"
            )

            assert result == "0xsigned_msg"

    @pytest.mark.asyncio
    async def test_close(self, dynamic_client):
        """Test closing client."""
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        dynamic_client._client = mock_client

        await dynamic_client.close()

        assert dynamic_client._client is None


class TestPrivyClient:
    """Test PrivyClient class."""

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
    def privy_client(self, privy_config):
        """Create PrivyClient instance."""
        return PrivyClient(privy_config)

    @pytest.mark.asyncio
    async def test_get_client_success(self, privy_client):
        """Test successful client creation."""
        with patch("app.services.wallet_providers.privy.client.AsyncPrivyAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api_class.return_value = mock_api

            client = await privy_client._get_client()

            assert client is not None

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, privy_client):
        """Test successful wallet creation."""
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.address = "0x123"

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.create = AsyncMock(return_value=mock_wallet)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.create_wallet("mainnet")

            assert result["wallet_id"] == "wallet_123"

    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, privy_client):
        """Test successful transaction signing."""
        mock_signed = MagicMock()
        mock_signed.transaction_hash = "0xsigned"

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.sign_transaction = AsyncMock(return_value=mock_signed)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.sign_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100"}
            )

            assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_message_success(self, privy_client):
        """Test successful message signing."""
        mock_signed = MagicMock()
        mock_signed.signature = "0xsigned_msg"

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.sign_message = AsyncMock(return_value=mock_signed)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.sign_message(wallet_id="wallet_123", message="test message")

            assert result == "0xsigned_msg"
