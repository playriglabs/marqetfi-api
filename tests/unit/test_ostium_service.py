"""Test Ostium service wrapper."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ostium_python_sdk import OstiumSDK
from web3 import Web3

from app.config.providers.ostium import OstiumConfig
from app.services.providers.exceptions import ServiceUnavailableError
from app.services.providers.ostium.base import OstiumService


class TestOstiumService:
    """Test OstiumService class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return OstiumConfig(
            private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            rpc_url="https://rpc.example.com",
            network="testnet",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def service(self, config):
        """Create test service."""
        return OstiumService(config)

    @pytest.mark.asyncio
    async def test_initialize_creates_sdk(self, service, config):
        """Test initialize creates SDK instance."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            mock_create.return_value = mock_sdk

            # Mock web3 creation
            with patch("app.services.providers.ostium.base.Web3") as mock_web3_class:
                mock_web3 = MagicMock(spec=Web3)
                mock_web3_class.return_value = mock_web3

                await service.initialize()

                assert service._initialized is True
                assert service._sdk == mock_sdk
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_uses_sdk_web3(self, service, config):
        """Test initialize uses web3 from SDK if available."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            mock_web3 = MagicMock(spec=Web3)
            mock_sdk.web3 = mock_web3
            mock_create.return_value = mock_sdk

            await service.initialize()

            assert service._web3 == mock_web3

    @pytest.mark.asyncio
    async def test_initialize_uses_sdk_w3(self, service, config):
        """Test initialize uses w3 from SDK if web3 not available."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            mock_web3 = MagicMock(spec=Web3)
            # SDK doesn't have web3, but has w3
            del mock_sdk.web3
            mock_sdk.w3 = mock_web3
            mock_create.return_value = mock_sdk

            await service.initialize()

            assert service._web3 == mock_web3

    @pytest.mark.asyncio
    async def test_initialize_creates_web3_if_not_in_sdk(self, service, config):
        """Test initialize creates web3 connection if SDK doesn't provide it."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            # SDK doesn't have web3 or w3
            del mock_sdk.web3
            del mock_sdk.w3
            mock_create.return_value = mock_sdk

            with patch("app.services.providers.ostium.base.Web3") as mock_web3_class:
                mock_web3 = MagicMock(spec=Web3)
                mock_web3_class.return_value = mock_web3

                await service.initialize()

                mock_web3_class.assert_called_once()
                assert service._web3 == mock_web3

    @pytest.mark.asyncio
    async def test_initialize_handles_web3_error_gracefully(self, service, config):
        """Test initialize handles web3 initialization errors gracefully."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            # Simulate error accessing web3
            mock_sdk.web3 = None
            type(mock_sdk).web3 = property(lambda self: None)
            mock_create.return_value = mock_sdk

            with patch(
                "app.services.providers.ostium.base.Web3", side_effect=Exception("Web3 error")
            ):
                await service.initialize()

                # Should still initialize, web3 will be created on demand
                assert service._initialized is True
                assert service._web3 is None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, service, config):
        """Test initialize is idempotent."""
        with patch.object(config, "create_sdk_instance") as mock_create:
            mock_sdk = MagicMock(spec=OstiumSDK)
            mock_create.return_value = mock_sdk

            with patch("app.services.providers.ostium.base.Web3"):
                await service.initialize()
                first_sdk = service._sdk

                await service.initialize()
                second_sdk = service._sdk

                # Should only create SDK once
                assert mock_create.call_count == 1
                assert first_sdk == second_sdk

    @pytest.mark.asyncio
    async def test_get_web3_returns_cached(self, service):
        """Test get_web3 returns cached web3 instance."""
        mock_web3 = MagicMock(spec=Web3)
        service._web3 = mock_web3

        result = service.get_web3()

        assert result == mock_web3

    @pytest.mark.asyncio
    async def test_get_web3_gets_from_sdk(self, service):
        """Test get_web3 gets web3 from SDK if not cached."""
        mock_sdk = MagicMock(spec=OstiumSDK)
        mock_web3 = MagicMock(spec=Web3)
        mock_sdk.web3 = mock_web3
        service._sdk = mock_sdk

        result = service.get_web3()

        assert result == mock_web3
        assert service._web3 == mock_web3

    @pytest.mark.asyncio
    async def test_get_web3_creates_new_connection(self, service, config):
        """Test get_web3 creates new connection if not available."""
        service._sdk = None
        config.rpc_url = "https://rpc.example.com"

        with patch("app.services.providers.ostium.base.Web3") as mock_web3_class:
            mock_web3 = MagicMock(spec=Web3)
            mock_web3_class.return_value = mock_web3

            result = service.get_web3()

            assert result == mock_web3
            mock_web3_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_web3_raises_error_no_rpc_url(self, service, config):
        """Test get_web3 raises error if RPC URL not configured."""
        service._sdk = None
        config.rpc_url = ""

        with pytest.raises(ServiceUnavailableError, match="RPC URL not configured"):
            service.get_web3()

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self, service):
        """Test health_check returns True when service is healthy."""
        mock_sdk = MagicMock(spec=OstiumSDK)
        mock_subgraph = MagicMock()
        mock_subgraph.get_pairs = AsyncMock(return_value=[])
        mock_sdk.subgraph = mock_subgraph
        service._sdk = mock_sdk
        service._initialized = True

        result = await service.health_check()

        assert result is True
        mock_subgraph.get_pairs.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_not_initialized(self, service):
        """Test health_check returns False when not initialized."""
        service._initialized = False

        result = await service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self, service):
        """Test health_check returns False on error."""
        mock_sdk = MagicMock(spec=OstiumSDK)
        mock_subgraph = MagicMock()
        mock_subgraph.get_pairs = AsyncMock(side_effect=Exception("Error"))
        mock_sdk.subgraph = mock_subgraph
        service._sdk = mock_sdk
        service._initialized = True

        result = await service.health_check()

        assert result is False

    def test_is_retryable_error_timeout(self, service):
        """Test _is_retryable_error identifies timeout errors."""
        error = TimeoutError("Request timeout")
        assert service._is_retryable_error(error) is True

    def test_is_retryable_error_connection(self, service):
        """Test _is_retryable_error identifies connection errors."""
        error = ConnectionError("Connection failed")
        assert service._is_retryable_error(error) is True

    def test_is_retryable_error_network(self, service):
        """Test _is_retryable_error identifies network errors."""
        error = Exception("Network error occurred")
        assert service._is_retryable_error(error) is True

    def test_is_retryable_error_rate_limit(self, service):
        """Test _is_retryable_error identifies rate limit errors."""
        error = Exception("Rate limit exceeded")
        assert service._is_retryable_error(error) is True

    def test_is_retryable_error_not_retryable_validation(self, service):
        """Test _is_retryable_error identifies non-retryable validation errors."""
        error = Exception("Validation error")
        assert service._is_retryable_error(error) is False

    def test_is_retryable_error_not_retryable_not_found(self, service):
        """Test _is_retryable_error identifies non-retryable not found errors."""
        error = Exception("Not found")
        assert service._is_retryable_error(error) is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, service):
        """Test _execute_with_retry succeeds on first attempt."""

        async def operation():
            return "success"

        result = await service._execute_with_retry(operation, "test_operation")

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_retries_on_retryable_error(self, service):
        """Test _execute_with_retry retries on retryable errors."""
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"

        result = await service._execute_with_retry(operation, "test_operation")

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_raises_non_retryable_error(self, service):
        """Test _execute_with_retry raises non-retryable errors immediately."""

        async def operation():
            raise ValueError("Validation error")

        with pytest.raises(ValueError, match="Validation error"):
            await service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausts_retries(self, service, config):
        """Test _execute_with_retry exhausts retries and raises error."""
        config.retry_attempts = 2

        async def operation():
            raise ConnectionError("Connection failed")

        with pytest.raises(ServiceUnavailableError, match="failed after 3 attempts"):
            await service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_handles_timeout(self, service, config):
        """Test _execute_with_retry handles timeout errors."""
        config.timeout = 0.1

        async def operation():
            await asyncio.sleep(1)
            return "success"

        with pytest.raises(ServiceUnavailableError, match="timed out"):
            await service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self, service):
        """Test _execute_with_retry handles sync functions."""

        def sync_operation():
            return "success"

        result = await service._execute_with_retry(sync_operation, "test_operation")

        assert result == "success"

    @pytest.mark.asyncio
    async def test_sdk_property_raises_when_not_initialized(self, service):
        """Test sdk property raises error when not initialized."""
        service._sdk = None

        with pytest.raises(ServiceUnavailableError, match="SDK not initialized"):
            _ = service.sdk
