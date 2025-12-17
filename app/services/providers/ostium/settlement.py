"""Ostium settlement provider implementation."""

from typing import Any

from app.config.providers.ostium import OstiumConfig
from app.services.providers.base import BaseSettlementProvider
from app.services.providers.exceptions import SettlementProviderError
from app.services.providers.ostium.base import OstiumService


class OstiumSettlementProvider(BaseSettlementProvider):
    """Ostium implementation of SettlementProvider."""

    def __init__(self, config: OstiumConfig):
        """Initialize Ostium settlement provider."""
        super().__init__("ostium-settlement")
        self.ostium_service = OstiumService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.ostium_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.ostium_service.health_check()

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
            await self.ostium_service.initialize()

            trade_params = {
                "collateral": collateral,
                "leverage": leverage,
                "asset_type": asset_type,
                "direction": direction,
                "order_type": order_type,
            }

            # Set slippage if configured
            if self.ostium_service.config.slippage_percentage:
                self.ostium_service.sdk.ostium.set_slippage_percentage(
                    self.ostium_service.config.slippage_percentage
                )

            import asyncio

            receipt = await asyncio.to_thread(
                self.ostium_service.sdk.ostium.perform_trade,
                trade_params,
                at_price=at_price,
            )

            return {
                "transaction_hash": receipt["transactionHash"].hex()
                if hasattr(receipt["transactionHash"], "hex")
                else str(receipt["transactionHash"]),
                "status": "executed",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "execute_trade")
            raise SettlementProviderError(
                str(error), service_name=self.service_name
            ) from e

    async def get_transaction_status(
        self, transaction_hash: str
    ) -> dict[str, Any]:
        """Get status of a transaction."""
        try:
            await self.ostium_service.initialize()

            # Note: Ostium SDK may not have direct transaction status check
            # This would need to be implemented based on SDK capabilities
            # For now, return a placeholder
            import asyncio

            # Try to get transaction receipt from web3
            # This is a placeholder - actual implementation depends on SDK
            return {
                "transaction_hash": transaction_hash,
                "status": "pending",  # Would need actual implementation
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(
                e, "get_transaction_status"
            )
            raise SettlementProviderError(
                str(error), service_name=self.service_name
            ) from e

