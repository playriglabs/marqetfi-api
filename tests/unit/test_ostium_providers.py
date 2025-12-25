"""Test Ostium provider implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.ostium import OstiumConfig
from app.services.providers.ostium.base import OstiumService
from app.services.providers.ostium.price import OstiumPriceProvider
from app.services.providers.ostium.settlement import OstiumSettlementProvider
from app.services.providers.ostium.trading import OstiumTradingProvider


class TestOstiumService:
    """Test OstiumService base class."""

    @pytest.fixture
    def ostium_config(self):
        """Create Ostium config."""
        return OstiumConfig(
            enabled=True,
            private_key="0x123",
            rpc_url="https://rpc.example.com",
            network="testnet",
            verbose=False,
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
        with patch("app.services.providers.ostium.base.asyncio.to_thread") as mock_thread:
            mock_sdk = MagicMock()
            mock_sdk.web3 = None
            mock_sdk.w3 = None
            mock_thread.return_value = mock_sdk

            with patch("app.services.providers.ostium.base.Web3") as mock_web3:
                mock_web3_instance = MagicMock()
                mock_web3.return_value = mock_web3_instance

                await ostium_service.initialize()

                assert ostium_service._initialized is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, ostium_service):
        """Test successful health check."""
        ostium_service._initialized = True
        ostium_service._sdk = MagicMock()

        result = await ostium_service.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, ostium_service):
        """Test health check when not initialized."""
        result = await ostium_service.health_check()
        assert result is False


class TestOstiumPriceProvider:
    """Test OstiumPriceProvider class."""

    @pytest.fixture
    def ostium_config(self):
        """Create Ostium config."""
        return OstiumConfig(
            enabled=True,
            private_key="0x123",
            rpc_url="https://rpc.example.com",
            network="testnet",
        )

    @pytest.fixture
    def price_provider(self, ostium_config):
        """Create OstiumPriceProvider instance."""
        return OstiumPriceProvider(ostium_config)

    @pytest.mark.asyncio
    async def test_get_price_success(self, price_provider):
        """Test getting price successfully."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "sdk") as mock_sdk:
            mock_price = MagicMock()
            mock_price.price.get_price = AsyncMock(return_value=(100.0, None))
            mock_sdk.__getattr__ = MagicMock(return_value=mock_price)

            with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
                mock_execute.return_value = (100.0, None)

                price, timestamp, source = await price_provider.get_price("BTC", "USDT")

                assert price == 100.0
                assert source == "ostium"

    @pytest.mark.asyncio
    async def test_get_prices_success(self, price_provider):
        """Test getting multiple prices."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = (100.0, None)

            result = await price_provider.get_prices([("BTC", "USDT")])

            assert "BTC/USDT" in result
            assert result["BTC/USDT"][0] == 100.0

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, price_provider):
        """Test getting trading pairs."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "sdk") as mock_sdk:
            mock_subgraph = MagicMock()
            mock_subgraph.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
            mock_sdk.subgraph = mock_subgraph

            pairs = await price_provider.get_pairs()

            assert len(pairs) == 1
            assert pairs[0]["pair_id"] == 1


class TestOstiumTradingProvider:
    """Test OstiumTradingProvider class."""

    @pytest.fixture
    def ostium_config(self):
        """Create Ostium config."""
        return OstiumConfig(
            enabled=True,
            private_key="0x123",
            rpc_url="https://rpc.example.com",
            network="testnet",
        )

    @pytest.fixture
    def trading_provider(self, ostium_config):
        """Create OstiumTradingProvider instance."""
        return OstiumTradingProvider(ostium_config)

    @pytest.mark.asyncio
    async def test_open_trade_success(self, trading_provider):
        """Test opening trade successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = "0x123"
            mock_execute.return_value = mock_receipt

            result = await trading_provider.open_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

            assert result["transaction_hash"] == "0x123"

    @pytest.mark.asyncio
    async def test_close_trade_success(self, trading_provider):
        """Test closing trade successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = "0x456"
            mock_execute.return_value = mock_receipt

            result = await trading_provider.close_trade(pair_id=1, index=0)

            assert result["status"] == "closed"

    @pytest.mark.asyncio
    async def test_get_open_trades_success(self, trading_provider):
        """Test getting open trades."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "sdk") as mock_sdk:
            mock_ostium = MagicMock()
            mock_ostium.get_open_trades = AsyncMock(return_value=[{"trade_id": "123"}])
            mock_sdk.ostium = mock_ostium

            result = await trading_provider.get_open_trades()

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, trading_provider):
        """Test getting trading pairs."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "sdk") as mock_sdk:
            mock_subgraph = MagicMock()
            mock_subgraph.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
            mock_sdk.subgraph = mock_subgraph

            pairs = await trading_provider.get_pairs()

            assert len(pairs) == 1


class TestOstiumSettlementProvider:
    """Test OstiumSettlementProvider class."""

    @pytest.fixture
    def ostium_config(self):
        """Create Ostium config."""
        return OstiumConfig(
            enabled=True,
            private_key="0x123",
            rpc_url="https://rpc.example.com",
            network="testnet",
        )

    @pytest.fixture
    def settlement_provider(self, ostium_config):
        """Create OstiumSettlementProvider instance."""
        return OstiumSettlementProvider(ostium_config)

    @pytest.mark.asyncio
    async def test_execute_trade_success(self, settlement_provider):
        """Test executing trade successfully."""
        await settlement_provider.initialize()

        with patch.object(
            settlement_provider.ostium_service, "_execute_with_retry"
        ) as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = "0x123"
            mock_execute.return_value = mock_receipt

            result = await settlement_provider.execute_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

            assert result["transaction_hash"] == "0x123"

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, settlement_provider):
        """Test getting transaction status."""
        await settlement_provider.initialize()

        with patch.object(settlement_provider.ostium_service, "_web3") as mock_web3:
            if mock_web3 is None:
                settlement_provider.ostium_service._web3 = MagicMock()
                mock_web3 = settlement_provider.ostium_service._web3

            mock_web3.eth.get_transaction_receipt = MagicMock(
                return_value={"status": 1, "blockNumber": 12345}
            )

            result = await settlement_provider.get_transaction_status("0x123")

            assert result["status"] == "confirmed"
            assert result["block_number"] == 12345
