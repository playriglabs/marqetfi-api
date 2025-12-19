"""Dynamic wallet provider implementation."""

from typing import Any, cast

from loguru import logger

from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.dynamic.client import DynamicClient
from app.services.wallet_providers.dynamic.config import DynamicWalletConfig
from app.services.wallet_providers.dynamic.exceptions import DynamicError
from app.services.wallet_providers.exceptions import (
    WalletCreationError,
    WalletNotFoundError,
    WalletSigningError,
)


class DynamicWalletProvider(BaseWalletProvider):
    """Dynamic wallet provider implementation."""

    def __init__(self, config: DynamicWalletConfig):
        """Initialize Dynamic wallet provider.

        Args:
            config: Dynamic configuration
        """
        super().__init__("dynamic")
        self.config = config
        self._client: DynamicClient | None = None

    async def initialize(self) -> None:
        """Initialize Dynamic client connection."""
        if self._initialized:
            return

        try:
            if not self.config.api_key:
                raise ValueError("Dynamic api_key is required")
            if not self.config.api_secret:
                raise ValueError("Dynamic api_secret is required")

            self._client = DynamicClient(self.config)
            self._initialized = True
            logger.info(f"{self.service_name} wallet provider initialized")
        except Exception as e:
            error = self.handle_service_error(e, "initialization")
            raise error from e

    async def health_check(self) -> bool:
        """Check if Dynamic service is healthy."""
        if not self._initialized or not self._client:
            return False

        try:
            # Try to get API status as health check
            # Note: Actual endpoint may vary based on Dynamic API
            await self._client._request("GET", "/v1/health")
            return True
        except Exception as e:
            logger.warning(f"{self.service_name} health check failed: {e}")
            return False

    @property
    def client(self) -> DynamicClient:
        """Get Dynamic client instance."""
        if not self._client:
            raise ValueError("Dynamic client not initialized")
        return self._client

    async def create_wallet(self, network: str) -> dict[str, Any]:
        """Create a new wallet.

        Args:
            network: Network name (testnet/mainnet)

        Returns:
            Dictionary containing wallet information
        """
        try:
            await self.initialize()
            response = await self.client.create_wallet(network)

            # Extract wallet information from response
            wallet_id = response.get("id") or response.get("wallet_id")
            address = response.get("address") or response.get("wallet_address")

            if not wallet_id or not address:
                raise WalletCreationError(
                    "Invalid response from Dynamic: missing wallet_id or address",
                    service_name=self.service_name,
                )

            return {
                "wallet_id": wallet_id,
                "address": address,
                "network": network,
                "metadata": response,
            }
        except DynamicError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "create_wallet")
            raise WalletCreationError(
                f"Failed to create wallet: {str(error)}",
                service_name=self.service_name,
            ) from error

    async def get_wallet_address(self, wallet_id: str) -> str:
        """Get wallet address for a given wallet ID.

        Args:
            wallet_id: Dynamic wallet ID

        Returns:
            Ethereum wallet address
        """
        try:
            await self.initialize()
            wallet_info = await self.client.get_wallet(wallet_id)
            address = wallet_info.get("address") or wallet_info.get("wallet_address")
            if not address:
                raise WalletNotFoundError(
                    f"Wallet address not found for wallet_id: {wallet_id}",
                    service_name=self.service_name,
                )
            return cast(str, address)
        except DynamicError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "get_wallet_address")
            raise WalletNotFoundError(
                f"Failed to get wallet address: {str(error)}",
                service_name=self.service_name,
            ) from error

    async def sign_transaction(self, wallet_id: str, transaction: dict[str, Any]) -> str:
        """Sign a transaction using the wallet.

        Args:
            wallet_id: Dynamic wallet ID
            transaction: Transaction dictionary

        Returns:
            Signed transaction hash or signature
        """
        try:
            await self.initialize()
            return await self.client.sign_transaction(wallet_id, transaction)
        except DynamicError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "sign_transaction")
            raise WalletSigningError(
                f"Failed to sign transaction: {str(error)}",
                service_name=self.service_name,
            ) from error

    async def sign_message(self, wallet_id: str, message: str) -> str:
        """Sign a message using the wallet.

        Args:
            wallet_id: Dynamic wallet ID
            message: Message to sign

        Returns:
            Message signature
        """
        try:
            await self.initialize()
            return await self.client.sign_message(wallet_id, message)
        except DynamicError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "sign_message")
            raise WalletSigningError(
                f"Failed to sign message: {str(error)}",
                service_name=self.service_name,
            ) from error

    async def get_wallet_info(self, wallet_id: str) -> dict[str, Any]:
        """Get wallet information.

        Args:
            wallet_id: Dynamic wallet ID

        Returns:
            Dictionary containing wallet information
        """
        try:
            await self.initialize()
            wallet_info = await self.client.get_wallet(wallet_id)
            return {
                "wallet_id": wallet_id,
                "address": wallet_info.get("address") or wallet_info.get("wallet_address"),
                "network": wallet_info.get("network", "mainnet"),
                "metadata": wallet_info,
            }
        except DynamicError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "get_wallet_info")
            raise WalletNotFoundError(
                f"Failed to get wallet info: {str(error)}",
                service_name=self.service_name,
            ) from error
