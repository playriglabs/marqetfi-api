"""Lighter settlement provider implementation."""

from typing import Any

from app.config.providers.lighter import LighterConfig
from app.services.providers.base import BaseSettlementProvider
from app.services.providers.exceptions import SettlementProviderError
from app.services.providers.lighter.base import LighterService

# Optional import for lighter SDK
try:
    import lighter
except ImportError:
    lighter = None  # type: ignore


class LighterSettlementProvider(BaseSettlementProvider):
    """Lighter implementation of SettlementProvider."""

    def __init__(self, config: LighterConfig):
        """Initialize Lighter settlement provider."""
        super().__init__("lighter-settlement")
        self.lighter_service = LighterService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.lighter_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.lighter_service.health_check()

    async def execute_trade(
        self,
        collateral: float,
        leverage: int,
        asset_type: int,
        direction: bool,
        order_type: str,
        at_price: float | None = None,
    ) -> dict[str, Any]:
        """Execute a trade."""
        try:
            if lighter is None:
                raise ImportError(
                    "lighter-python is not installed. Install with: "
                    "pip install git+https://github.com/elliottech/lighter-python.git"
                )

            await self.lighter_service.initialize()

            import asyncio

            order_api = lighter.OrderApi(self.lighter_service.client)

            # Map parameters to Lighter order format
            order_data = {
                "amount": collateral,
                "side": "buy" if direction else "sell",
                "order_type": order_type.lower(),
            }

            if at_price:
                order_data["price"] = at_price

            result = await asyncio.to_thread(order_api.create_order, order_data)

            return {
                "transaction_hash": str(result.get("id", "")),
                "status": "executed",
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "execute_trade")
            raise SettlementProviderError(str(error), service_name=self.service_name) from e

    async def get_transaction_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a transaction."""
        try:
            if lighter is None:
                raise ImportError(
                    "lighter-python is not installed. Install with: "
                    "pip install git+https://github.com/elliottech/lighter-python.git"
                )

            await self.lighter_service.initialize()

            import asyncio

            order_api = lighter.OrderApi(self.lighter_service.client)

            # Get order status by ID
            order = await asyncio.to_thread(order_api.get_order, order_id=transaction_hash)

            return {
                "transaction_hash": transaction_hash,
                "status": order.get("status", "unknown"),
                "order": order,
            }
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_transaction_status")
            raise SettlementProviderError(str(error), service_name=self.service_name) from e
