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

            # Set slippage before each trade (as per SDK examples)
            # Default to 1% if not configured (matching SDK example)
            slippage = self.ostium_service.config.slippage_percentage or 1.0
            self.ostium_service.sdk.ostium.set_slippage_percentage(slippage)

            receipt = await self.ostium_service._execute_with_retry(
                self.ostium_service.sdk.ostium.perform_trade,
                "execute_trade",
                trade_params,
                at_price=at_price,
            )

            return {
                "transaction_hash": (
                    receipt["transactionHash"].hex()
                    if hasattr(receipt["transactionHash"], "hex")
                    else str(receipt["transactionHash"])
                ),
                "status": "executed",
            }
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "execute_trade")
            raise SettlementProviderError(str(error), service_name=self.service_name) from e

    async def get_transaction_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a transaction.

        Args:
            transaction_hash: The transaction hash to check

        Returns:
            Dictionary containing:
            - transaction_hash: The transaction hash
            - status: Transaction status ('pending', 'confirmed', 'failed', 'not_found')
            - block_number: Block number if confirmed (optional)
            - block_hash: Block hash if confirmed (optional)
            - gas_used: Gas used if confirmed (optional)
            - confirmations: Number of confirmations (optional)
        """
        try:
            await self.ostium_service.initialize()

            # Get web3 instance
            web3 = self.ostium_service.get_web3()

            # Normalize transaction hash (remove 0x prefix if needed, ensure it's hex)
            tx_hash = transaction_hash
            if not tx_hash.startswith("0x"):
                tx_hash = f"0x{tx_hash}"

            # Check if transaction exists with retry logic
            try:
                tx = await self.ostium_service._execute_with_retry(
                    web3.eth.get_transaction,
                    "get_transaction",
                    tx_hash,
                )
            except Exception as tx_error:
                # Transaction not found or invalid hash
                error_msg = str(tx_error).lower()
                if "not found" in error_msg or "invalid" in error_msg:
                    return {
                        "transaction_hash": transaction_hash,
                        "status": "not_found",
                    }
                raise

            # Try to get transaction receipt (only exists if transaction was mined)
            try:
                receipt = await self.ostium_service._execute_with_retry(
                    web3.eth.get_transaction_receipt,
                    "get_transaction_receipt",
                    tx_hash,
                )

                # Transaction was mined - check status
                status = "confirmed" if receipt.get("status") == 1 else "failed"

                # Get current block number for confirmation count
                current_block = await self.ostium_service._execute_with_retry(
                    lambda: web3.eth.block_number,
                    "get_block_number",
                )
                confirmations = max(0, current_block - receipt.get("blockNumber", 0))

                result = {
                    "transaction_hash": transaction_hash,
                    "status": status,
                    "block_number": receipt.get("blockNumber"),
                    "block_hash": (
                        receipt.get("blockHash").hex()  # type: ignore[union-attr]
                        if receipt.get("blockHash")
                        else None
                    ),
                    "gas_used": receipt.get("gasUsed"),
                    "confirmations": confirmations,
                }

                # Add transaction details
                if tx:
                    result["from"] = tx.get("from")
                    result["to"] = tx.get("to")
                    result["value"] = str(tx.get("value", 0))

                return result
            except Exception as receipt_error:
                # Receipt not found means transaction is pending
                error_msg = str(receipt_error).lower()
                if "not found" in error_msg:
                    # Transaction exists but not yet mined
                    return {
                        "transaction_hash": transaction_hash,
                        "status": "pending",
                        "from": tx.get("from") if tx else None,
                        "to": tx.get("to") if tx else None,
                    }
                raise

        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_transaction_status")
            raise SettlementProviderError(str(error), service_name=self.service_name) from e
