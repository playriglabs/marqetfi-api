"""Wallet service for high-level wallet operations."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.ostium_wallet_repository import OstiumWalletRepository
from app.services.wallet_providers.exceptions import (
    WalletCreationError,
    WalletNotFoundError,
    WalletSigningError,
)
from app.services.wallet_providers.factory import WalletProviderFactory


class WalletService:
    """High-level wallet service."""

    def __init__(self, db: AsyncSession):
        """Initialize wallet service.

        Args:
            db: Database session
        """
        self.db = db
        self.repository = OstiumWalletRepository()

    async def create_wallet(
        self, provider_name: str, network: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a new wallet using the specified provider.

        Args:
            provider_name: Provider name (privy/dynamic)
            network: Network name (testnet/mainnet)
            metadata: Optional additional metadata

        Returns:
            Dictionary containing wallet information including database ID

        Raises:
            WalletCreationError: If wallet creation fails
        """
        # Get provider and create wallet
        provider = await WalletProviderFactory.get_provider(provider_name)
        wallet_data = await provider.create_wallet(network)

        wallet_id = wallet_data.get("wallet_id")
        address = wallet_data.get("address")

        if not wallet_id or not address:
            raise WalletCreationError(
                "Invalid wallet data from provider",
                service_name="wallet_service",
            )

        # Check if wallet already exists
        existing = await self.repository.get_by_provider_wallet_id(self.db, wallet_id)
        if existing:
            return {
                "id": existing.id,
                "provider_type": existing.provider_type,
                "provider_wallet_id": existing.provider_wallet_id,
                "wallet_address": existing.wallet_address,
                "network": existing.network,
                "is_active": existing.is_active,
                "metadata": existing.metadata or {},
            }

        # Store in database
        wallet_record = await self.repository.create(
            self.db,
            {
                "provider_type": provider_name,
                "provider_wallet_id": wallet_id,
                "wallet_address": address,
                "network": network,
                "is_active": True,
                "metadata": {**(wallet_data.get("metadata", {})), **(metadata or {})},
            },
        )

        return {
            "id": wallet_record.id,
            "provider_type": wallet_record.provider_type,
            "provider_wallet_id": wallet_record.provider_wallet_id,
            "wallet_address": wallet_record.wallet_address,
            "network": wallet_record.network,
            "is_active": wallet_record.is_active,
            "metadata": wallet_record.metadata or {},
        }

    async def get_wallet(self, wallet_id: int) -> dict[str, Any]:
        """Get wallet by database ID.

        Args:
            wallet_id: Database wallet ID

        Returns:
            Wallet information

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = await self.repository.get(self.db, wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {wallet_id}",
                service_name="wallet_service",
            )

        return {
            "id": wallet.id,
            "provider_type": wallet.provider_type,
            "provider_wallet_id": wallet.provider_wallet_id,
            "wallet_address": wallet.wallet_address,
            "network": wallet.network,
            "is_active": wallet.is_active,
            "metadata": wallet.metadata or {},
        }

    async def get_wallet_by_provider_id(self, provider_wallet_id: str) -> dict[str, Any]:
        """Get wallet by provider wallet ID.

        Args:
            provider_wallet_id: Provider-specific wallet ID

        Returns:
            Wallet information

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = await self.repository.get_by_provider_wallet_id(self.db, provider_wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {provider_wallet_id}",
                service_name="wallet_service",
            )

        return {
            "id": wallet.id,
            "provider_type": wallet.provider_type,
            "provider_wallet_id": wallet.provider_wallet_id,
            "wallet_address": wallet.wallet_address,
            "network": wallet.network,
            "is_active": wallet.is_active,
            "metadata": wallet.metadata or {},
        }

    async def sign_transaction(self, wallet_id: int, transaction: dict[str, Any]) -> str:
        """Sign a transaction using the wallet.

        Args:
            wallet_id: Database wallet ID
            transaction: Transaction dictionary

        Returns:
            Signed transaction hash or signature

        Raises:
            WalletNotFoundError: If wallet not found
            WalletSigningError: If signing fails
        """
        wallet = await self.repository.get(self.db, wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {wallet_id}",
                service_name="wallet_service",
            )

        if not wallet.is_active:
            raise WalletSigningError(
                f"Wallet is not active: {wallet_id}",
                service_name="wallet_service",
            )

        # Get provider and sign transaction
        provider = await WalletProviderFactory.get_provider(wallet.provider_type)
        try:
            return await provider.sign_transaction(wallet.provider_wallet_id, transaction)
        except Exception as e:
            raise WalletSigningError(
                f"Failed to sign transaction: {str(e)}",
                service_name="wallet_service",
            ) from e

    async def sign_message(self, wallet_id: int, message: str) -> str:
        """Sign a message using the wallet.

        Args:
            wallet_id: Database wallet ID
            message: Message to sign

        Returns:
            Message signature

        Raises:
            WalletNotFoundError: If wallet not found
            WalletSigningError: If signing fails
        """
        wallet = await self.repository.get(self.db, wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {wallet_id}",
                service_name="wallet_service",
            )

        if not wallet.is_active:
            raise WalletSigningError(
                f"Wallet is not active: {wallet_id}",
                service_name="wallet_service",
            )

        # Get provider and sign message
        provider = await WalletProviderFactory.get_provider(wallet.provider_type)
        try:
            return await provider.sign_message(wallet.provider_wallet_id, message)
        except Exception as e:
            raise WalletSigningError(
                f"Failed to sign message: {str(e)}",
                service_name="wallet_service",
            ) from e

    async def get_active_wallet(self, provider_name: str, network: str) -> dict[str, Any] | None:
        """Get an active wallet for the specified provider and network.

        Args:
            provider_name: Provider name (privy/dynamic)
            network: Network name (testnet/mainnet)

        Returns:
            Wallet information or None if no active wallet found
        """
        wallets = await self.repository.get_active_by_provider(self.db, provider_name, network)
        if not wallets:
            return None

        # Return the first active wallet
        wallet = wallets[0]
        return {
            "id": wallet.id,
            "provider_type": wallet.provider_type,
            "provider_wallet_id": wallet.provider_wallet_id,
            "wallet_address": wallet.wallet_address,
            "network": wallet.network,
            "is_active": wallet.is_active,
            "metadata": wallet.metadata or {},
        }

    async def list_wallets(
        self, provider_name: str | None = None, network: str | None = None
    ) -> list[dict[str, Any]]:
        """List wallets with optional filters.

        Args:
            provider_name: Optional provider filter
            network: Optional network filter

        Returns:
            List of wallet information
        """
        if provider_name and network:
            wallets = await self.repository.get_by_provider_and_network(
                self.db, provider_name, network
            )
        else:
            wallets = await self.repository.get_all(self.db)

        return [
            {
                "id": wallet.id,
                "provider_type": wallet.provider_type,
                "provider_wallet_id": wallet.provider_wallet_id,
                "wallet_address": wallet.wallet_address,
                "network": wallet.network,
                "is_active": wallet.is_active,
                "metadata": wallet.metadata or {},
            }
            for wallet in wallets
        ]

    async def deactivate_wallet(self, wallet_id: int) -> dict[str, Any]:
        """Deactivate a wallet.

        Args:
            wallet_id: Database wallet ID

        Returns:
            Updated wallet information

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = await self.repository.deactivate(self.db, wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {wallet_id}",
                service_name="wallet_service",
            )

        return {
            "id": wallet.id,
            "provider_type": wallet.provider_type,
            "provider_wallet_id": wallet.provider_wallet_id,
            "wallet_address": wallet.wallet_address,
            "network": wallet.network,
            "is_active": wallet.is_active,
            "metadata": wallet.metadata or {},
        }

    async def activate_wallet(self, wallet_id: int) -> dict[str, Any]:
        """Activate a wallet.

        Args:
            wallet_id: Database wallet ID

        Returns:
            Updated wallet information

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = await self.repository.activate(self.db, wallet_id)
        if not wallet:
            raise WalletNotFoundError(
                f"Wallet not found: {wallet_id}",
                service_name="wallet_service",
            )

        return {
            "id": wallet.id,
            "provider_type": wallet.provider_type,
            "provider_wallet_id": wallet.provider_wallet_id,
            "wallet_address": wallet.wallet_address,
            "network": wallet.network,
            "is_active": wallet.is_active,
            "metadata": wallet.metadata or {},
        }
