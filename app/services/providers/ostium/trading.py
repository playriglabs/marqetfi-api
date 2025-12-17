"""Ostium trading provider implementation."""

from typing import Any

from app.config.providers.ostium import OstiumConfig
from app.services.providers.base import BaseTradingProvider
from app.services.providers.exceptions import TradingProviderError
from app.services.providers.ostium.base import OstiumService


class OstiumTradingProvider(BaseTradingProvider):
    """Ostium implementation of TradingProvider."""

    def __init__(self, config: OstiumConfig):
        """Initialize Ostium trading provider."""
        super().__init__("ostium-trading")
        self.ostium_service = OstiumService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.ostium_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.ostium_service.health_check()

    async def open_trade(
        self,
        collateral: float,
        leverage: int,
        asset_type: int,
        direction: bool,
        order_type: str,
        at_price: float | None = None,
        tp: float | None = None,
        sl: float | None = None,
    ) -> dict[str, Any]:
        """Open a new trade."""
        try:
            await self.ostium_service.initialize()

            trade_params = {
                "collateral": collateral,
                "leverage": leverage,
                "asset_type": asset_type,
                "direction": direction,
                "order_type": order_type,
            }

            if tp:
                trade_params["tp"] = tp
            if sl:
                trade_params["sl"] = sl

            # Set slippage if configured
            if self.ostium_service.config.slippage_percentage:
                self.ostium_service.sdk.ostium.set_slippage_percentage(
                    self.ostium_service.config.slippage_percentage
                )

            # Execute trade
            import asyncio

            receipt = await asyncio.to_thread(
                self.ostium_service.sdk.ostium.perform_trade,
                trade_params,
                at_price=at_price,
            )

            return {
                "transaction_hash": (
                    receipt["transactionHash"].hex()
                    if hasattr(receipt["transactionHash"], "hex")
                    else str(receipt["transactionHash"])
                ),
                "status": "success",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "open_trade")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def close_trade(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Close an existing trade."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            receipt = await asyncio.to_thread(
                self.ostium_service.sdk.ostium.close_trade, pair_id, trade_index
            )

            return {
                "transaction_hash": (
                    receipt["transactionHash"].hex()
                    if hasattr(receipt["transactionHash"], "hex")
                    else str(receipt["transactionHash"])
                ),
                "status": "closed",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "close_trade")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_tp(self, pair_id: int, trade_index: int, tp_price: float) -> dict[str, Any]:
        """Update take profit for a trade."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            await asyncio.to_thread(
                self.ostium_service.sdk.ostium.update_tp, pair_id, trade_index, tp_price
            )

            return {"status": "updated", "tp_price": tp_price}
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "update_tp")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_sl(self, pair_id: int, trade_index: int, sl_price: float) -> dict[str, Any]:
        """Update stop loss for a trade."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            await asyncio.to_thread(
                self.ostium_service.sdk.ostium.update_sl, pair_id, trade_index, sl_price
            )

            return {"status": "updated", "sl_price": sl_price}
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "update_sl")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_open_trades(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open trades for a trader."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            trades = await asyncio.to_thread(
                self.ostium_service.sdk.subgraph.get_open_trades, trader_address
            )

            return list(trades) if trades else []
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_open_trades")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_open_trade_metrics(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Get metrics for an open trade."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            metrics = await asyncio.to_thread(
                self.ostium_service.sdk.get_open_trade_metrics, pair_id, trade_index
            )

            return dict(metrics) if metrics else {}
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_open_trade_metrics")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_orders(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open orders for a trader."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            orders = await asyncio.to_thread(
                self.ostium_service.sdk.subgraph.get_orders, trader_address
            )

            return list(orders) if orders else []
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_orders")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def cancel_limit_order(self, pair_id: int, order_index: int) -> dict[str, Any]:
        """Cancel a limit order."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            receipt = await asyncio.to_thread(
                self.ostium_service.sdk.ostium.cancel_limit_order, pair_id, order_index
            )

            return {
                "transaction_hash": (
                    receipt["transactionHash"].hex()
                    if hasattr(receipt["transactionHash"], "hex")
                    else str(receipt["transactionHash"])
                ),
                "status": "cancelled",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "cancel_limit_order")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_limit_order(
        self,
        pair_id: int,
        order_index: int,
        at_price: float,
    ) -> dict[str, Any]:
        """Update a limit order."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            receipt = await asyncio.to_thread(
                self.ostium_service.sdk.ostium.update_limit_order,
                pair_id,
                order_index,
                at_price,
            )

            return {
                "transaction_hash": (
                    receipt["transactionHash"].hex()
                    if hasattr(receipt["transactionHash"], "hex")
                    else str(receipt["transactionHash"])
                ),
                "status": "updated",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "update_limit_order")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            pairs = await asyncio.to_thread(self.ostium_service.sdk.subgraph.get_pairs)

            return list(pairs) if pairs else []
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_pairs")
            raise TradingProviderError(str(error), service_name=self.service_name) from e
