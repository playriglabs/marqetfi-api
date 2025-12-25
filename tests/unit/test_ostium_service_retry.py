"""Test OstiumService retry logic."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.config.providers.ostium import OstiumConfig
from app.services.providers.exceptions import ServiceUnavailableError
from app.services.providers.ostium.base import OstiumService


class TestOstiumServiceRetry:
    """Test OstiumService retry logic."""

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
            retry_attempts=2,
            retry_delay=0.1,
        )

    @pytest.fixture
    def ostium_service(self, ostium_config):
        """Create OstiumService instance."""
        return OstiumService(ostium_config)

    def test_is_retryable_error_timeout(self, ostium_service):
        """Test retryable error detection for timeout."""
        error = TimeoutError("Request timeout")
        result = ostium_service._is_retryable_error(error)

        assert result is True

    def test_is_retryable_error_connection(self, ostium_service):
        """Test retryable error detection for connection error."""
        error = ConnectionError("Connection failed")
        result = ostium_service._is_retryable_error(error)

        assert result is True

    def test_is_retryable_error_rate_limit(self, ostium_service):
        """Test retryable error detection for rate limit."""
        error = Exception("Rate limit exceeded")
        result = ostium_service._is_retryable_error(error)

        assert result is True

    def test_is_retryable_error_validation(self, ostium_service):
        """Test non-retryable error detection for validation."""
        error = ValueError("Invalid input")
        result = ostium_service._is_retryable_error(error)

        assert result is False

    def test_is_retryable_error_unauthorized(self, ostium_service):
        """Test non-retryable error detection for unauthorized."""
        error = Exception("401 Unauthorized")
        result = ostium_service._is_retryable_error(error)

        assert result is False

    def test_is_retryable_error_not_found(self, ostium_service):
        """Test non-retryable error detection for not found."""
        error = Exception("404 Not found")
        result = ostium_service._is_retryable_error(error)

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, ostium_service):
        """Test successful execution without retry."""

        async def operation():
            return "success"

        result = await ostium_service._execute_with_retry(operation, "test_operation")

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self, ostium_service):
        """Test successful execution after retry."""
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await ostium_service._execute_with_retry(operation, "test_operation")

            assert result == "success"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_timeout(self, ostium_service):
        """Test execution timeout."""

        async def operation():
            await asyncio.sleep(100)  # Will timeout
            return "success"

        with pytest.raises(ServiceUnavailableError, match="timed out"):
            await ostium_service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, ostium_service):
        """Test execution with non-retryable error."""

        async def operation():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            await ostium_service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self, ostium_service):
        """Test execution when retries are exhausted."""

        async def operation():
            raise ConnectionError("Connection failed")

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(ServiceUnavailableError, match="failed after"),
        ):
            await ostium_service._execute_with_retry(operation, "test_operation")

    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self, ostium_service):
        """Test execution with sync function."""

        def sync_operation():
            return "success"

        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value="success"):
            result = await ostium_service._execute_with_retry(sync_operation, "test_operation")

            assert result == "success"
