"""Settlement service for trade execution."""

from typing import Any

from app.services.providers.base import BaseSettlementProvider
from app.services.providers.router import get_provider_router


class SettlementService:
    """Service for trade settlement operations."""

    def __init__(self, settlement_provider: BaseSettlementProvider | None = None):
        """Initialize settlement service.

        If settlement_provider is None, uses ProviderRouter for multi-provider support.
        """
        self.settlement_provider = settlement_provider
        self.router = get_provider_router() if settlement_provider is None else None

    async def execute_trade(
        self,
        collateral: float,
        leverage: int,
        asset_type: int,
        direction: bool,
        order_type: str,
        at_price: float | None = None,
        asset: str | None = None,
    ) -> dict[str, Any]:
        """Execute a trade."""
        # Validation
        if collateral <= 0:
            raise ValueError("Collateral must be greater than 0")
        if leverage < 1:
            raise ValueError("Leverage must be at least 1")

        # Get provider based on asset type or asset symbol
        if self.router:
            provider = await self.router.get_settlement_provider(asset=asset, asset_type=asset_type)
        else:
            if self.settlement_provider is None:
                raise ValueError("Settlement provider not configured")
            provider = self.settlement_provider

        receipt = await provider.execute_trade(
            collateral=collateral,
            leverage=leverage,
            asset_type=asset_type,
            direction=direction,
            order_type=order_type,
            at_price=at_price,
        )

        # Store transaction receipt (would integrate with database here)
        return receipt

    async def get_transaction_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a transaction."""
        if self.settlement_provider is None:
            raise ValueError("Settlement provider not configured")
        return await self.settlement_provider.get_transaction_status(transaction_hash)
