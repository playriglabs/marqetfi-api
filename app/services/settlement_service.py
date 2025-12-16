"""Settlement service for trade execution."""

from typing import Any

from app.services.providers.base import BaseSettlementProvider


class SettlementService:
    """Service for trade settlement operations."""

    def __init__(self, settlement_provider: BaseSettlementProvider):
        """Initialize settlement service."""
        self.settlement_provider = settlement_provider

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
        # Validation
        if collateral <= 0:
            raise ValueError("Collateral must be greater than 0")
        if leverage < 1:
            raise ValueError("Leverage must be at least 1")

        receipt = await self.settlement_provider.execute_trade(
            collateral=collateral,
            leverage=leverage,
            asset_type=asset_type,
            direction=direction,
            order_type=order_type,
            at_price=at_price,
        )

        # Store transaction receipt (would integrate with database here)
        return receipt

    async def get_transaction_status(
        self, transaction_hash: str
    ) -> dict[str, Any]:
        """Get status of a transaction."""
        return await self.settlement_provider.get_transaction_status(transaction_hash)

