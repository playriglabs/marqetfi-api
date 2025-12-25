"""Extended tests for wallet provider clients."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.wallet_providers.dynamic.client import DynamicClient
from app.services.wallet_providers.dynamic.config import DynamicWalletConfig
from app.services.wallet_providers.dynamic.exceptions import (
    DynamicAPIError,
    DynamicAuthenticationError,
    DynamicRateLimitError,
)
from app.services.wallet_providers.privy.client import PrivyClient
from app.services.wallet_providers.privy.config import PrivyWalletConfig
from app.services.wallet_providers.privy.exceptions import (
    PrivyAPIError,
    PrivyAuthenticationError,
    PrivyRateLimitError,
)


class TestDynamicClientExtended:
    """Extended tests for DynamicClient."""

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
    async def test_request_authentication_error(self, dynamic_client):
        """Test request with authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(dynamic_client, "_get_client") as mock_get_client:
            mock_http_client = MagicMock()
            mock_http_client.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=mock_response
                )
            )
            mock_get_client.return_value = mock_http_client

            with pytest.raises(DynamicAuthenticationError):
                await dynamic_client._request("GET", "/v1/wallets")

    @pytest.mark.asyncio
    async def test_request_rate_limit_error(self, dynamic_client):
        """Test request with rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with (
            patch.object(dynamic_client, "_get_client") as mock_get_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_http_client = MagicMock()
            mock_http_client.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "429", request=MagicMock(), response=mock_response
                )
            )
            mock_get_client.return_value = mock_http_client

            with pytest.raises(DynamicRateLimitError):
                await dynamic_client._request("GET", "/v1/wallets")

    @pytest.mark.asyncio
    async def test_request_timeout_retry(self, dynamic_client):
        """Test request with timeout and retry."""
        with (
            patch.object(dynamic_client, "_get_client") as mock_get_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_http_client = MagicMock()
            mock_http_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_http_client

            with pytest.raises(DynamicAPIError):
                await dynamic_client._request("GET", "/v1/wallets")

            # Should retry multiple times
            assert mock_http_client.request.call_count > 1

    @pytest.mark.asyncio
    async def test_request_connection_error_retry(self, dynamic_client):
        """Test request with connection error and retry."""
        with (
            patch.object(dynamic_client, "_get_client") as mock_get_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_http_client = MagicMock()
            mock_http_client.request = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )
            mock_get_client.return_value = mock_http_client

            with pytest.raises(DynamicAPIError):
                await dynamic_client._request("GET", "/v1/wallets")

            # Should retry multiple times
            assert mock_http_client.request.call_count > 1

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, dynamic_client):
        """Test getting wallet successfully."""
        with patch.object(dynamic_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "wallet_123", "address": "0x123"}

            result = await dynamic_client.get_wallet("wallet_123")

            assert result["id"] == "wallet_123"
            mock_request.assert_called_once_with("GET", "/v1/wallets/wallet_123")

    @pytest.mark.asyncio
    async def test_sign_transaction_with_signature(self, dynamic_client):
        """Test signing transaction with signature field."""
        with patch.object(dynamic_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"signature": "0xsigned"}

            result = await dynamic_client.sign_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100"}
            )

            assert result == "0xsigned"


class TestPrivyClientExtended:
    """Extended tests for PrivyClient."""

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
    async def test_handle_error_authentication(self, privy_client):
        """Test error handling for authentication error."""
        from app.services.wallet_providers.privy.client import AuthenticationError

        error = AuthenticationError("Authentication failed")

        with pytest.raises(PrivyAuthenticationError):
            privy_client._handle_error(error)

    @pytest.mark.asyncio
    async def test_handle_error_rate_limit(self, privy_client):
        """Test error handling for rate limit error."""
        from app.services.wallet_providers.privy.client import RateLimitError

        error = RateLimitError("Rate limit exceeded")

        with pytest.raises(PrivyRateLimitError):
            privy_client._handle_error(error)

    @pytest.mark.asyncio
    async def test_handle_error_connection(self, privy_client):
        """Test error handling for connection error."""
        from app.services.wallet_providers.privy.client import APIConnectionError

        error = APIConnectionError("Connection failed")

        with pytest.raises(PrivyAPIError):
            privy_client._handle_error(error)

    @pytest.mark.asyncio
    async def test_handle_error_api_status(self, privy_client):
        """Test error handling for API status error."""
        from app.services.wallet_providers.privy.client import APIStatusError

        error = APIStatusError("API error")
        error.status_code = 500

        with pytest.raises(PrivyAPIError):
            privy_client._handle_error(error)

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, privy_client):
        """Test getting wallet successfully."""
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.address = "0x123"
        mock_wallet.to_dict = MagicMock(return_value={"id": "wallet_123", "address": "0x123"})

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.get = AsyncMock(return_value=mock_wallet)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.get_wallet("wallet_123")

            assert result["id"] == "wallet_123"

    @pytest.mark.asyncio
    async def test_get_wallet_without_to_dict(self, privy_client):
        """Test getting wallet without to_dict method."""
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.address = "0x123"
        mock_wallet.chain_type = "ethereum"
        mock_wallet.owner = "user_123"

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.get = AsyncMock(return_value=mock_wallet)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.get_wallet("wallet_123")

            assert result["id"] == "wallet_123"
            assert result["address"] == "0x123"

    @pytest.mark.asyncio
    async def test_sign_transaction_with_dict_result(self, privy_client):
        """Test signing transaction with dict result."""
        mock_result = {"signature": "0xsigned"}

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.rpc = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.sign_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100", "chainId": 1}
            )

            assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_transaction_with_string_result(self, privy_client):
        """Test signing transaction with string result."""
        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.rpc = AsyncMock(return_value="0xsigned")
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.sign_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100", "chainId": 1}
            )

            assert result == "0xsigned"

    @pytest.mark.asyncio
    async def test_sign_message_with_dict_result(self, privy_client):
        """Test signing message with dict result."""
        mock_result = {"signature": "0xsigned_msg"}

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.rpc = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.sign_message(wallet_id="wallet_123", message="test message")

            assert result == "0xsigned_msg"

    @pytest.mark.asyncio
    async def test_send_transaction_success(self, privy_client):
        """Test sending transaction successfully."""
        mock_result = MagicMock()
        mock_result.to_dict = MagicMock(return_value={"transaction_hash": "0xsent"})

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.rpc = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.send_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100", "chainId": 1}
            )

            assert result["transaction_hash"] == "0xsent"
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_transaction_with_dict_result(self, privy_client):
        """Test sending transaction with dict result."""
        mock_result = {"transaction_hash": "0xsent"}

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.rpc = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.send_transaction(
                wallet_id="wallet_123", transaction={"to": "0xabc", "value": "100", "chainId": 1}
            )

            assert result["transaction_hash"] == "0xsent"

    @pytest.mark.asyncio
    async def test_close_success(self, privy_client):
        """Test closing client successfully."""
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        privy_client._client = mock_client

        await privy_client.close()

        assert privy_client._client is None

    @pytest.mark.asyncio
    async def test_create_wallet_with_to_dict(self, privy_client):
        """Test creating wallet with to_dict method."""
        mock_wallet = MagicMock()
        mock_wallet.to_dict = MagicMock(
            return_value={"id": "wallet_123", "address": "0x123", "chain_type": "ethereum"}
        )

        with patch.object(privy_client, "_get_client") as mock_get_client:
            mock_sdk_client = MagicMock()
            mock_sdk_client.wallets.create = AsyncMock(return_value=mock_wallet)
            mock_get_client.return_value = mock_sdk_client

            result = await privy_client.create_wallet("mainnet")

            assert result["wallet_id"] == "wallet_123"
            assert result["address"] == "0x123"
