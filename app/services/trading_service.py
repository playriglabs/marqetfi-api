"""Trading service for order management."""

from typing import Any

from app.services.providers.base import BaseTradingProvider
from app.services.providers.router import get_provider_router


class TradingService:
    """Service for trading operations."""

    def __init__(self, trading_provider: BaseTradingProvider | None = None):
        """Initialize trading service.

        If trading_provider is None, uses ProviderRouter for multi-provider support.
        """
        self.trading_provider = trading_provider
        self.router = get_provider_router() if trading_provider is None else None

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
        asset: str | None = None,
    ) -> dict[str, Any]:
        """Open a new trade."""
        # Business logic validation
        if collateral <= 0:
            raise ValueError("Collateral must be greater than 0")
        if leverage < 1:
            raise ValueError("Leverage must be at least 1")
        if order_type not in ["MARKET", "LIMIT", "STOP"]:
            raise ValueError("Order type must be MARKET, LIMIT, or STOP")

        # Get provider based on asset type or asset symbol
        if self.router:
            provider = await self.router.get_trading_provider(asset=asset, asset_type=asset_type)
        else:
            if self.trading_provider is None:
                raise ValueError("Trading provider not configured")
            provider = self.trading_provider

        return await provider.open_trade(
            collateral=collateral,
            leverage=leverage,
            asset_type=asset_type,
            direction=direction,
            order_type=order_type,
            at_price=at_price,
            tp=tp,
            sl=sl,
        )

    async def close_trade(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Close an existing trade."""
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.close_trade(pair_id, trade_index)

    async def update_tp(self, pair_id: int, trade_index: int, tp_price: float) -> dict[str, Any]:
        """Update take profit for a trade."""
        if tp_price <= 0:
            raise ValueError("Take profit price must be greater than 0")
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.update_tp(pair_id, trade_index, tp_price)

    async def update_sl(self, pair_id: int, trade_index: int, sl_price: float) -> dict[str, Any]:
        """Update stop loss for a trade."""
        if sl_price <= 0:
            raise ValueError("Stop loss price must be greater than 0")
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.update_sl(pair_id, trade_index, sl_price)

    async def get_open_trades(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open trades for a trader."""
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.get_open_trades(trader_address)

    async def get_open_trade_metrics(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Get metrics for an open trade."""
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.get_open_trade_metrics(pair_id, trade_index)

    async def get_orders(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open orders for a trader."""
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.get_orders(trader_address)

    async def cancel_limit_order(self, pair_id: int, order_index: int) -> dict[str, Any]:
        """Cancel a limit order."""
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.cancel_limit_order(pair_id, order_index)

    async def update_limit_order(
        self, pair_id: int, order_index: int, at_price: float
    ) -> dict[str, Any]:
        """Update a limit order."""
        if at_price <= 0:
            raise ValueError("Order price must be greater than 0")
        if self.trading_provider is None:
            raise ValueError("Trading provider not configured")
        return await self.trading_provider.update_limit_order(pair_id, order_index, at_price)

    async def get_pairs(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get all available trading pairs.

        Args:
            category: Optional category filter (crypto, forex, indices, commodities)
        """
        if self.router and category:
            # Get provider for category
            provider_name = self.router._category_provider_map.get(category.lower(), "ostium")
            from app.services.providers.factory import ProviderFactory

            provider = await ProviderFactory.get_trading_provider(provider_name)
            return await provider.get_pairs()
        elif self.router:
            # Get pairs from all providers
            all_pairs = []
            for provider_name in ["lighter", "ostium"]:
                try:
                    from app.services.providers.factory import ProviderFactory

                    provider = await ProviderFactory.get_trading_provider(provider_name)
                    pairs = await provider.get_pairs()
                    # Tag pairs with provider
                    for pair in pairs:
                        pair["provider"] = provider_name
                    all_pairs.extend(pairs)
                except Exception:
                    continue
            return all_pairs
        else:
            if self.trading_provider is None:
                raise ValueError("Trading provider not configured")
            return await self.trading_provider.get_pairs()
