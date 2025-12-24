"""Privy wallet provider implementation."""

from typing import Any, cast

from loguru import logger

from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.exceptions import (
    WalletCreationError,
    WalletNotFoundError,
    WalletSigningError,
)
from app.services.wallet_providers.privy.client import PrivyClient
from app.services.wallet_providers.privy.config import PrivyWalletConfig
from app.services.wallet_providers.privy.exceptions import PrivyError


class PrivyWalletProvider(BaseWalletProvider):
    """Privy wallet provider implementation."""

    def __init__(self, config: PrivyWalletConfig):
        """Initialize Privy wallet provider.

        Args:
            config: Privy configuration
        """
        super().__init__("privy")
        self.config = config
        self._client: PrivyClient | None = None

    async def initialize(self) -> None:
        """Initialize Privy client connection."""
        if self._initialized:
            return

        try:
            if not self.config.app_id:
                raise ValueError("Privy app_id is required")
            if not self.config.app_secret:
                raise ValueError("Privy app_secret is required")

            self._client = PrivyClient(self.config)
            self._initialized = True
            logger.info(f"{self.service_name} wallet provider initialized")
        except Exception as e:
            error = self.handle_service_error(e, "initialization")
            raise error from e

    async def health_check(self) -> bool:
        """Check if Privy service is healthy."""
        if not self._initialized or not self._client:
            return False

        try:
            # Verify the client is initialized and can be accessed
            # The SDK client should be available if initialization succeeded
            client = await self._client._get_client()
            if client is None:
                return False

            # Try a lightweight operation to verify connectivity
            # Note: This is a basic check - actual health verification
            # may require calling a specific health endpoint if available
            return True
        except Exception as e:
            logger.warning(f"{self.service_name} health check failed: {e}")
            return False

    @property
    def client(self) -> PrivyClient:
        """Get Privy client instance."""
        if not self._client:
            raise ValueError("Privy client not initialized")
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
                    "Invalid response from Privy: missing wallet_id or address",
                    service_name=self.service_name,
                )

            return {
                "wallet_id": wallet_id,
                "address": address,
                "network": network,
                "metadata": response,
            }
        except PrivyError:
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
            wallet_id: Privy wallet ID

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
        except PrivyError:
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
            wallet_id: Privy wallet ID
            transaction: Transaction dictionary

        Returns:
            Signed transaction hash or signature
        """
        try:
            await self.initialize()
            return await self.client.sign_transaction(wallet_id, transaction)
        except PrivyError:
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
            wallet_id: Privy wallet ID
            message: Message to sign

        Returns:
            Message signature
        """
        try:
            await self.initialize()
            return await self.client.sign_message(wallet_id, message)
        except PrivyError:
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
            wallet_id: Privy wallet ID

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
        except PrivyError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "get_wallet_info")
            raise WalletNotFoundError(
                f"Failed to get wallet info: {str(error)}",
                service_name=self.service_name,
            ) from error

    async def send_transaction(self, wallet_id: str, transaction: dict[str, Any]) -> dict[str, Any]:
        """Send a signed transaction via Privy API.

        Args:
            wallet_id: Privy wallet ID
            transaction: Transaction dictionary

        Returns:
            Transaction receipt with transaction_hash
        """
        try:
            await self.initialize()
            return await self.client.send_transaction(wallet_id, transaction)
        except PrivyError:
            raise
        except Exception as e:
            error = self.handle_service_error(e, "send_transaction")
            raise WalletSigningError(
                f"Failed to send transaction: {str(error)}",
                service_name=self.service_name,
            ) from error
