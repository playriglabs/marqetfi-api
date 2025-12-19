"""Dynamic API client wrapper."""

import asyncio
from typing import Any, cast

import httpx
from loguru import logger

from app.services.wallet_providers.dynamic.config import DynamicWalletConfig
from app.services.wallet_providers.dynamic.exceptions import (
    DynamicAPIError,
    DynamicAuthenticationError,
    DynamicRateLimitError,
)


class DynamicClient:
    """Client for interacting with Dynamic API."""

    def __init__(self, config: DynamicWalletConfig):
        """Initialize Dynamic client.

        Args:
            config: Dynamic configuration
        """
        self.config = config
        self.base_url = config.api_url.rstrip("/")
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Note: Dynamic.xyz does not have an official Python SDK,
        so we use direct HTTP requests to their REST API.
        """
        if self._client is None:
            # Dynamic API authentication may vary - adjust headers as needed
            # based on actual Dynamic API documentation
            headers = {
                "Content-Type": "application/json",
            }

            # Add authentication headers
            if self.api_secret:
                headers["Authorization"] = f"Bearer {self.api_secret}"
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json: Request body
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            DynamicAPIError: For API errors
            DynamicAuthenticationError: For authentication errors
            DynamicRateLimitError: For rate limit errors
        """
        client = await self._get_client()
        max_attempts = self.config.retry_attempts + 1
        retry_delay = self.config.retry_delay

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.request(
                    method,
                    endpoint,
                    json=json,
                    params=params,
                )
                response.raise_for_status()
                return cast(dict[str, Any], response.json())

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise DynamicAuthenticationError(
                        f"Dynamic authentication failed: {e.response.text}",
                        service_name="dynamic",
                    ) from e
                if e.response.status_code == 429:
                    if attempt < max_attempts:
                        await asyncio.sleep(retry_delay * attempt)
                        continue
                    raise DynamicRateLimitError(
                        f"Dynamic rate limit exceeded: {e.response.text}",
                        service_name="dynamic",
                    ) from e
                # Non-retryable error
                raise DynamicAPIError(
                    f"Dynamic API error: {e.response.status_code} - {e.response.text}",
                    service_name="dynamic",
                ) from e

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_attempts:
                    logger.warning(
                        f"Dynamic request failed (attempt {attempt}/{max_attempts}): {e}"
                    )
                    await asyncio.sleep(retry_delay * attempt)
                    continue
                raise DynamicAPIError(
                    f"Dynamic request failed after {max_attempts} attempts: {str(e)}",
                    service_name="dynamic",
                ) from e

            except Exception as e:
                last_error = e
                raise DynamicAPIError(
                    f"Unexpected Dynamic error: {str(e)}",
                    service_name="dynamic",
                ) from e

        if last_error:
            raise DynamicAPIError(
                f"Dynamic request failed: {str(last_error)}",
                service_name="dynamic",
            ) from last_error

        raise DynamicAPIError("Dynamic request failed", service_name="dynamic")

    async def create_wallet(self, network: str) -> dict[str, Any]:
        """Create a new wallet via Dynamic API.

        Args:
            network: Network name (testnet/mainnet)

        Returns:
            Wallet information
        """
        # Dynamic API endpoint for creating wallets
        # Note: Actual endpoint may vary based on Dynamic API documentation
        endpoint = "/v1/wallets"
        data = {
            "network": network,
            "environment": self.config.environment,
        }
        return await self._request("POST", endpoint, json=data)

    async def get_wallet(self, wallet_id: str) -> dict[str, Any]:
        """Get wallet information.

        Args:
            wallet_id: Dynamic wallet ID

        Returns:
            Wallet information
        """
        endpoint = f"/v1/wallets/{wallet_id}"
        return await self._request("GET", endpoint)

    async def sign_transaction(self, wallet_id: str, transaction: dict[str, Any]) -> str:
        """Sign a transaction via Dynamic API.

        Args:
            wallet_id: Dynamic wallet ID
            transaction: Transaction data

        Returns:
            Signed transaction hash
        """
        endpoint = f"/v1/wallets/{wallet_id}/sign-transaction"
        response = await self._request("POST", endpoint, json={"transaction": transaction})
        return cast(str, response.get("signature") or response.get("transaction_hash", ""))

    async def sign_message(self, wallet_id: str, message: str) -> str:
        """Sign a message via Dynamic API.

        Args:
            wallet_id: Dynamic wallet ID
            message: Message to sign

        Returns:
            Message signature
        """
        endpoint = f"/v1/wallets/{wallet_id}/sign-message"
        response = await self._request("POST", endpoint, json={"message": message})
        return cast(str, response.get("signature", ""))
