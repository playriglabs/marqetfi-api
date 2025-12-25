"""Test LighterSettlementProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.lighter import LighterConfig
from app.services.providers.lighter.settlement import LighterSettlementProvider


class TestLighterSettlementProvider:
    """Test LighterSettlementProvider class."""

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
    def settlement_provider(self, lighter_config):
        """Create LighterSettlementProvider instance."""
        return LighterSettlementProvider(lighter_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, settlement_provider):
        """Test successful initialization."""
        with patch.object(
            settlement_provider.lighter_service, "initialize", new_callable=AsyncMock
        ):
            await settlement_provider.initialize()

            settlement_provider.lighter_service.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, settlement_provider):
        """Test successful health check."""
        with patch.object(
            settlement_provider.lighter_service,
            "health_check",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await settlement_provider.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_execute_trade_success(self, settlement_provider):
        """Test successful trade execution."""
        mock_order_api = MagicMock()
        mock_order_api.create_order = MagicMock(return_value={"id": "order_123"})

        with (
            patch("app.services.providers.lighter.settlement.lighter") as mock_lighter,
            patch.object(settlement_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch.object(settlement_provider.lighter_service, "client", new_callable=MagicMock),
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value={"id": "order_123"}),
        ):
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)
            settlement_provider.lighter_service._client = MagicMock()

            result = await settlement_provider.execute_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

            assert result["status"] == "executed"
            assert "transaction_hash" in result

    @pytest.mark.asyncio
    async def test_execute_trade_sdk_not_installed(self, settlement_provider):
        """Test trade execution when SDK not installed."""
        with patch("app.services.providers.lighter.settlement.lighter", None):
            with pytest.raises(Exception, match="lighter-python is not installed"):
                await settlement_provider.execute_trade(
                    collateral=1000.0,
                    leverage=10,
                    asset_type=1,
                    direction=True,
                    order_type="MARKET",
                )

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, settlement_provider):
        """Test successful transaction status retrieval."""
        mock_order_api = MagicMock()
        mock_order_api.get_order = MagicMock(return_value={"id": "order_123", "status": "filled"})

        with (
            patch("app.services.providers.lighter.settlement.lighter") as mock_lighter,
            patch.object(settlement_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch.object(settlement_provider.lighter_service, "client", new_callable=MagicMock),
            patch(
                "asyncio.to_thread",
                new_callable=AsyncMock,
                return_value={"id": "order_123", "status": "filled"},
            ),
        ):
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)
            settlement_provider.lighter_service._client = MagicMock()

            result = await settlement_provider.get_transaction_status("order_123")

            assert result["status"] == "filled"
            assert result["transaction_hash"] == "order_123"
