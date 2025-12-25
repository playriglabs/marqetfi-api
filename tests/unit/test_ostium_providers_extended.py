"""Extended tests for Ostium provider implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.ostium import OstiumConfig
from app.services.providers.ostium.price import OstiumPriceProvider
from app.services.providers.ostium.trading import OstiumTradingProvider


class TestOstiumTradingProviderExtended:
    """Extended tests for OstiumTradingProvider."""

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
    async def test_update_tp_success(self, trading_provider):
        """Test updating take profit successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = "0x789"
            mock_execute.return_value = mock_receipt

            result = await trading_provider.update_tp(pair_id=1, trade_index=0, tp_price=50000.0)

            assert result["status"] == "updated"
            assert result["transaction_hash"] == "0x789"

    @pytest.mark.asyncio
    async def test_update_sl_success(self, trading_provider):
        """Test updating stop loss successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = "0xabc"
            mock_execute.return_value = mock_receipt

            result = await trading_provider.update_sl(pair_id=1, trade_index=0, sl_price=40000.0)

            assert result["status"] == "updated"
            assert result["transaction_hash"] == "0xabc"

    @pytest.mark.asyncio
    async def test_get_open_trade_metrics_success(self, trading_provider):
        """Test getting open trade metrics."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "sdk") as mock_sdk:
            mock_ostium = MagicMock()
            mock_ostium.get_open_trade_metrics = AsyncMock(
                return_value={"pnl": 100.0, "leverage": 10, "collateral": 1000.0}
            )
            mock_sdk.ostium = mock_ostium

            with patch.object(
                trading_provider.ostium_service, "_execute_with_retry"
            ) as mock_execute:
                mock_execute.return_value = {"pnl": 100.0, "leverage": 10, "collateral": 1000.0}

                result = await trading_provider.get_open_trade_metrics(pair_id=1, trade_index=0)

                assert result["pnl"] == 100.0
                assert result["leverage"] == 10

    @pytest.mark.asyncio
    async def test_get_orders_success(self, trading_provider):
        """Test getting orders."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "sdk") as mock_sdk:
            mock_ostium = MagicMock()
            mock_ostium.get_orders = AsyncMock(
                return_value=[{"order_id": "123", "status": "pending"}]
            )
            mock_sdk.ostium = mock_ostium

            with patch.object(
                trading_provider.ostium_service, "_execute_with_retry"
            ) as mock_execute:
                mock_execute.return_value = [{"order_id": "123", "status": "pending"}]

                result = await trading_provider.get_orders("0x1234567890abcdef")

                assert len(result) == 1
                assert result[0]["order_id"] == "123"

    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self, trading_provider):
        """Test cancelling limit order successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = MagicMock()
            mock_receipt.transactionHash.hex = MagicMock(return_value="0xdef")
            mock_execute.return_value = mock_receipt

            result = await trading_provider.cancel_limit_order(pair_id=1, order_index=0)

            assert result["status"] == "cancelled"
            assert result["transaction_hash"] == "0xdef"

    @pytest.mark.asyncio
    async def test_update_limit_order_success(self, trading_provider):
        """Test updating limit order successfully."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_receipt = MagicMock()
            mock_receipt.transactionHash = MagicMock()
            mock_receipt.transactionHash.hex = MagicMock(return_value="0xghi")
            mock_execute.return_value = mock_receipt

            result = await trading_provider.update_limit_order(
                pair_id=1, order_index=0, at_price=45000.0
            )

            assert result["status"] == "updated"
            assert result["transaction_hash"] == "0xghi"

    @pytest.mark.asyncio
    async def test_get_pair_details_success(self, trading_provider):
        """Test getting pair details."""
        await trading_provider.initialize()

        with patch.object(trading_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = {
                "pair_id": "1",
                "symbol": "BTCUSDT",
                "base": "BTC",
                "quote": "USDT",
            }

            result = await trading_provider.get_pair_details("1")

            assert result["pair_id"] == "1"
            assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_parse_order_details_success(self, trading_provider):
        """Test parsing order details."""
        with patch(
            "app.services.providers.ostium.trading.get_order_details"
        ) as mock_get_order_details:
            mock_get_order_details.return_value = (
                1,
                None,
                None,
                None,
                None,
                None,
                None,
                2,
                3,
                None,
                None,
            )

            order_data = {"raw": "data"}
            result = trading_provider.parse_order_details(order_data)

            assert result["limit_type"] == 1
            assert result["pair_index"] == 2
            assert result["index"] == 3
            assert result["raw_data"] == order_data

    @pytest.mark.asyncio
    async def test_parse_order_details_error(self, trading_provider):
        """Test parsing order details with error."""
        with patch(
            "app.services.providers.ostium.trading.get_order_details"
        ) as mock_get_order_details:
            mock_get_order_details.side_effect = Exception("Parse error")

            order_data = {"raw": "data"}
            result = trading_provider.parse_order_details(order_data)

            assert result["raw_data"] == order_data
            assert "parse_error" in result


class TestOstiumPriceProviderExtended:
    """Extended tests for OstiumPriceProvider."""

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
    async def test_get_price_three_value_return(self, price_provider):
        """Test getting price with 3-value return."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = (100.0, 1234567890, "ostium")

            price, timestamp, source = await price_provider.get_price("BTC", "USDT")

            assert price == 100.0
            assert timestamp == 1234567890
            assert source == "ostium"

    @pytest.mark.asyncio
    async def test_get_price_single_value_return(self, price_provider):
        """Test getting price with single value return."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = 100.0

            price, timestamp, source = await price_provider.get_price("BTC", "USDT")

            assert price == 100.0
            assert source == "ostium"

    @pytest.mark.asyncio
    async def test_get_prices_with_exceptions(self, price_provider):
        """Test getting prices with some exceptions."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.side_effect = [
                (100.0, None),  # First succeeds
                Exception("Price fetch failed"),  # Second fails
                (200.0, None),  # Third succeeds
            ]

            result = await price_provider.get_prices(
                [("BTC", "USDT"), ("ETH", "USDT"), ("SOL", "USDT")]
            )

            assert "BTC/USDT" in result
            assert "SOL/USDT" in result
            assert "ETH/USDT" not in result  # Failed

    @pytest.mark.asyncio
    async def test_get_prices_three_value_returns(self, price_provider):
        """Test getting prices with 3-value returns."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = (100.0, 1234567890, "ostium")

            result = await price_provider.get_prices([("BTC", "USDT")])

            assert "BTC/USDT" in result
            assert result["BTC/USDT"] == (100.0, 1234567890, "ostium")

    @pytest.mark.asyncio
    async def test_get_prices_single_value_returns(self, price_provider):
        """Test getting prices with single value returns."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = 100.0

            result = await price_provider.get_prices([("BTC", "USDT")])

            assert "BTC/USDT" in result
            assert result["BTC/USDT"][0] == 100.0
            assert result["BTC/USDT"][2] == "ostium"

    @pytest.mark.asyncio
    async def test_get_pair_details_success(self, price_provider):
        """Test getting pair details."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = {
                "pair_id": "1",
                "symbol": "BTCUSDT",
                "base": "BTC",
                "quote": "USDT",
            }

            result = await price_provider.get_pair_details("1")

            assert result["pair_id"] == "1"
            assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_get_pair_details_empty(self, price_provider):
        """Test getting pair details when empty."""
        await price_provider.initialize()

        with patch.object(price_provider.ostium_service, "_execute_with_retry") as mock_execute:
            mock_execute.return_value = None

            result = await price_provider.get_pair_details("1")

            assert result == {}
