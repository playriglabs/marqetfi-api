"""Test LifiSwapProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config.providers.lifi import LifiConfig
from app.services.providers.lifi.base import LifiSwapProvider


class TestLifiSwapProvider:
    """Test LifiSwapProvider class."""

    @pytest.fixture
    def lifi_config(self):
        """Create LIFI config."""
        return LifiConfig(
            enabled=True,
            api_url="https://li.xyz/v1",
            api_key="test_key",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def swap_provider(self, lifi_config):
        """Create LifiSwapProvider instance."""
        return LifiSwapProvider(lifi_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, swap_provider):
        """Test successful initialization."""
        await swap_provider.initialize()

        assert swap_provider._initialized is True
        assert swap_provider.client is not None

    @pytest.mark.asyncio
    async def test_initialize_with_api_key(self, lifi_config):
        """Test initialization with API key."""
        lifi_config.api_key = "test_key"
        provider = LifiSwapProvider(lifi_config)

        await provider.initialize()

        assert provider.client is not None
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self, lifi_config):
        """Test initialization without API key."""
        lifi_config.api_key = None
        provider = LifiSwapProvider(lifi_config)

        await provider.initialize()

        assert provider.client is not None
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, swap_provider):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await swap_provider.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, swap_provider):
        """Test health check failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await swap_provider.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, swap_provider):
        """Test health check with exception."""
        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(side_effect=Exception("Connection error"))

            result = await swap_provider.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_get_swap_quote_success(self, swap_provider):
        """Test getting swap quote successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "estimate": {"toAmount": "99.5"},
            "fee": {"amount": "0.5"},
            "transactionRequest": {"data": "0x123"},
            "action": {"validity": {"from": 1234567890, "to": 1234567890}},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await swap_provider.get_swap_quote(
                from_token="0xUSDT",
                to_token="0xUSDC",
                from_chain="arbitrum",
                to_chain="ethereum",
                amount="100.0",
            )

            assert result["estimated_amount"] == "99.5"
            assert "fee" in result
            assert "transaction" in result

    @pytest.mark.asyncio
    async def test_get_swap_quote_http_error(self, swap_provider):
        """Test getting swap quote with HTTP error."""
        from app.services.providers.exceptions import ExternalServiceError

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ExternalServiceError):
                await swap_provider.get_swap_quote(
                    from_token="0xUSDT",
                    to_token="0xUSDC",
                    from_chain="arbitrum",
                    to_chain="ethereum",
                    amount="100.0",
                )

    @pytest.mark.asyncio
    async def test_execute_swap_success(self, swap_provider):
        """Test executing swap successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "txHash": "0xswap123",
            "status": "pending",
            "estimatedCompletion": 1234567890,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            quote = {"quote_data": {"action": {}}}
            result = await swap_provider.execute_swap(quote, "0xwallet123")

            assert result["transaction_hash"] == "0xswap123"
            assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_execute_swap_with_transaction_hash(self, swap_provider):
        """Test executing swap with transactionHash field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "transactionHash": "0xswap456",
            "status": "pending",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            quote = {"quote_data": {"action": {}}}
            result = await swap_provider.execute_swap(quote, "0xwallet123")

            assert result["transaction_hash"] == "0xswap456"

    @pytest.mark.asyncio
    async def test_get_swap_status_success(self, swap_provider):
        """Test getting swap status successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "completed",
            "fromAmount": "100.0",
            "toAmount": "99.5",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await swap_provider.get_swap_status("0xswap123")

            assert result["status"] == "completed"
            assert result["transaction_hash"] == "0xswap123"
            assert result["from_amount"] == "100.0"
            assert result["to_amount"] == "99.5"

    @pytest.mark.asyncio
    async def test_get_swap_status_with_error(self, swap_provider):
        """Test getting swap status with error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "failed",
            "error": "Swap failed",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(swap_provider, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await swap_provider.get_swap_status("0xswap123")

            assert result["status"] == "failed"
            assert result["error"] == "Swap failed"
