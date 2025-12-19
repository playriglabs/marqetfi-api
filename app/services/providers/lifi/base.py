"""LI-FI swap provider implementation."""

from typing import Any

import httpx

from app.config.providers.lifi import LifiConfig
from app.services.providers.base import BaseSwapProvider
from app.services.providers.exceptions import ExternalServiceError


class LifiSwapProvider(BaseSwapProvider):
    """LI-FI implementation of SwapProvider."""

    def __init__(self, config: LifiConfig):
        """Initialize LI-FI swap provider."""
        super().__init__("lifi-swap")
        self.config = config
        self.client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.config.api_url,
                timeout=self.config.timeout,
                headers={"X-API-Key": self.config.api_key} if self.config.api_key else {},
            )
        self._initialized = True

    async def health_check(self) -> bool:
        """Check provider health."""
        try:
            await self.initialize()
            # LI-FI health check endpoint (adjust if different)
            response = await self.client.get("/health")  # type: ignore[union-attr]
            return bool(response.status_code == 200)
        except Exception:
            return False

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        from_chain: str,
        to_chain: str,
        amount: str,
    ) -> dict[str, Any]:
        """Get a quote for a token swap.

        Args:
            from_token: Source token address
            to_token: Destination token address
            from_chain: Source chain identifier (chain ID as string)
            to_chain: Destination chain identifier (chain ID as string)
            amount: Amount to swap (as string to preserve precision)

        Returns:
            Dictionary containing quote information
        """
        try:
            await self.initialize()

            # LI-FI quote endpoint
            # Adjust endpoint and parameters based on actual LI-FI API
            params = {
                "fromChain": from_chain,
                "toChain": to_chain,
                "fromToken": from_token,
                "toToken": to_token,
                "fromAmount": amount,
            }

            response = await self.client.get("/quote", params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            quote_data = response.json()

            return {
                "estimated_amount": quote_data.get("estimate", {}).get("toAmount", "0"),
                "fee": quote_data.get("fee", {}),
                "transaction": quote_data.get("transactionRequest", {}),
                "validity": quote_data.get("action", {}).get("validity", {}),
                "quote_data": quote_data,  # Store full quote for execution
            }
        except httpx.HTTPStatusError as e:
            error = self.handle_service_error(e, "get_swap_quote")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e
        except Exception as e:
            error = self.handle_service_error(e, "get_swap_quote")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e

    async def execute_swap(
        self,
        quote: dict[str, Any],
        wallet_address: str,
    ) -> dict[str, Any]:
        """Execute a token swap.

        Args:
            quote: Quote data from get_swap_quote
            wallet_address: Wallet address to execute swap from

        Returns:
            Dictionary containing transaction hash and status
        """
        try:
            await self.initialize()

            # LI-FI execute swap endpoint
            # This typically requires signing the transaction on the client side
            # For now, return the transaction data that needs to be signed
            quote_data = quote.get("quote_data", {})

            # If LI-FI provides a way to execute directly, use that
            # Otherwise, return transaction data for client to sign
            payload = {
                "walletAddress": wallet_address,
                "quote": quote_data,
            }

            response = await self.client.post("/swap", json=payload)  # type: ignore[union-attr]
            response.raise_for_status()
            result = response.json()

            return {
                "transaction_hash": result.get("txHash") or result.get("transactionHash", ""),
                "status": result.get("status", "pending"),
                "estimated_completion": result.get("estimatedCompletion"),
            }
        except httpx.HTTPStatusError as e:
            error = self.handle_service_error(e, "execute_swap")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e
        except Exception as e:
            error = self.handle_service_error(e, "execute_swap")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e

    async def get_swap_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a swap transaction.

        Args:
            transaction_hash: Transaction hash from execute_swap

        Returns:
            Dictionary containing swap status
        """
        try:
            await self.initialize()

            # LI-FI status endpoint
            response = await self.client.get(f"/status/{transaction_hash}")  # type: ignore[union-attr]
            response.raise_for_status()
            status_data = response.json()

            return {
                "status": status_data.get("status", "unknown"),
                "transaction_hash": transaction_hash,
                "from_amount": status_data.get("fromAmount"),
                "to_amount": status_data.get("toAmount"),
                "error": status_data.get("error"),
            }
        except httpx.HTTPStatusError as e:
            error = self.handle_service_error(e, "get_swap_status")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e
        except Exception as e:
            error = self.handle_service_error(e, "get_swap_status")
            raise ExternalServiceError(str(error), service_name=self.service_name) from e
