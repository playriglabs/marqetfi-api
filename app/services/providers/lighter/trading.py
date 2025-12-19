"""Lighter trading provider implementation."""

from typing import Any

from app.config.providers.lighter import LighterConfig
from app.services.providers.base import BaseTradingProvider
from app.services.providers.exceptions import TradingProviderError
from app.services.providers.lighter.base import LighterService

# Optional import for lighter SDK
try:
    import lighter
except ImportError:
    lighter = None  # type: ignore


class LighterTradingProvider(BaseTradingProvider):
    """Lighter implementation of TradingProvider."""

    def __init__(self, config: LighterConfig):
        """Initialize Lighter trading provider."""
        super().__init__("lighter-trading")
        self.lighter_service = LighterService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.lighter_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.lighter_service.health_check()

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
            if lighter is None:
                raise ImportError(
                    "lighter-python is not installed. Install with: "
                    "pip install git+https://github.com/elliottech/lighter-python.git"
                )

            await self.lighter_service.initialize()

            import asyncio

            # Get OrderApi from Lighter SDK
            order_api = lighter.OrderApi(self.lighter_service.client)

            # Map our parameters to Lighter's order format
            # Note: This is a placeholder - adjust based on actual Lighter API
            # Lighter may use different parameter names/format
            order_data = {
                "amount": collateral,
                "side": "buy" if direction else "sell",
                "order_type": order_type.lower(),
            }

            if at_price:
                order_data["price"] = at_price

            # Create order
            result = await asyncio.to_thread(order_api.create_order, order_data)  # type: ignore[attr-defined]

            return {
                "transaction_hash": str(result.get("id", "")),
                "status": "success",
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "open_trade")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def close_trade(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Close an existing trade."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            order_api = lighter.OrderApi(self.lighter_service.client)

            # Cancel order (Lighter may use order ID instead of pair_id/index)
            result = await asyncio.to_thread(order_api.cancel_order, order_id=str(trade_index))  # type: ignore[attr-defined]

            return {
                "transaction_hash": str(result.get("id", "")),
                "status": "closed",
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "close_trade")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_tp(self, pair_id: int, trade_index: int, tp_price: float) -> dict[str, Any]:
        """Update take profit for a trade."""
        try:
            await self.lighter_service.initialize()

            # Lighter may not support TP/SL updates directly
            # This would need to be implemented based on actual SDK capabilities
            return {"status": "not_supported", "message": "TP update not supported by Lighter"}
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "update_tp")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_sl(self, pair_id: int, trade_index: int, sl_price: float) -> dict[str, Any]:
        """Update stop loss for a trade."""
        try:
            await self.lighter_service.initialize()

            # Lighter may not support TP/SL updates directly
            return {"status": "not_supported", "message": "SL update not supported by Lighter"}
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "update_sl")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_open_trades(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open trades for a trader."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            account_api = lighter.AccountApi(self.lighter_service.client)

            # Get account by address
            account = await asyncio.to_thread(
                account_api.account, by="address", value=trader_address
            )

            # Get open positions/orders from account
            # This is a placeholder - adjust based on actual account structure
            return [{"account": account, "status": "open"}]
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_open_trades")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_open_trade_metrics(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Get metrics for an open trade."""
        try:
            await self.lighter_service.initialize()

            # Placeholder - implement based on Lighter's actual metrics API
            return {"status": "not_implemented"}
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_open_trade_metrics")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_orders(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open orders for a trader."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            order_api = lighter.OrderApi(self.lighter_service.client)

            # Get orders for account
            # This is a placeholder - adjust based on actual API
            orders = await asyncio.to_thread(order_api.get_orders, account=trader_address)  # type: ignore[attr-defined]

            return list(orders) if orders else []
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_orders")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def cancel_limit_order(self, pair_id: int, order_index: int) -> dict[str, Any]:
        """Cancel a limit order."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            order_api = lighter.OrderApi(self.lighter_service.client)

            result = await asyncio.to_thread(order_api.cancel_order, order_id=str(order_index))  # type: ignore[attr-defined]

            return {
                "transaction_hash": str(result.get("id", "")),
                "status": "cancelled",
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "cancel_limit_order")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def update_limit_order(
        self,
        pair_id: int,
        order_index: int,
        at_price: float,
    ) -> dict[str, Any]:
        """Update a limit order."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            order_api = lighter.OrderApi(self.lighter_service.client)

            # Update order - adjust based on actual API
            result = await asyncio.to_thread(
                order_api.update_order,  # type: ignore[attr-defined]
                order_id=str(order_index),
                price=at_price,
            )

            return {
                "transaction_hash": str(result.get("id", "")),
                "status": "updated",
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "update_limit_order")
            raise TradingProviderError(str(error), service_name=self.service_name) from e

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            # Get markets/pairs from Lighter API
            # This is a placeholder - adjust based on actual API
            market_api = lighter.MarketApi(self.lighter_service.client)  # type: ignore[attr-defined]
            markets = await asyncio.to_thread(market_api.get_markets)

            return list(markets) if markets else []
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_pairs")
            raise TradingProviderError(str(error), service_name=self.service_name) from e
