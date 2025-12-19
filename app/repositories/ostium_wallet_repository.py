"""Ostium wallet repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import OstiumWallet
from app.repositories.base import BaseRepository


class OstiumWalletRepository(BaseRepository[OstiumWallet]):
    """Repository for Ostium wallet operations."""

    def __init__(self) -> None:
        """Initialize repository."""
        super().__init__(OstiumWallet)

    async def get_by_provider_wallet_id(
        self, db: AsyncSession, provider_wallet_id: str
    ) -> OstiumWallet | None:
        """Get wallet by provider wallet ID.

        Args:
            db: Database session
            provider_wallet_id: Provider-specific wallet ID

        Returns:
            Wallet or None if not found
        """
        result = await db.execute(
            select(OstiumWallet).where(OstiumWallet.provider_wallet_id == provider_wallet_id)
        )
        return result.scalar_one_or_none()

    async def get_by_address(
        self, db: AsyncSession, wallet_address: str, network: str | None = None
    ) -> OstiumWallet | None:
        """Get wallet by address.

        Args:
            db: Database session
            wallet_address: Ethereum wallet address
            network: Optional network filter

        Returns:
            Wallet or None if not found
        """
        query = select(OstiumWallet).where(OstiumWallet.wallet_address == wallet_address)
        if network:
            query = query.where(OstiumWallet.network == network)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_provider(
        self, db: AsyncSession, provider_type: str, network: str
    ) -> list[OstiumWallet]:
        """Get active wallets by provider and network.

        Args:
            db: Database session
            provider_type: Provider type (privy/dynamic)
            network: Network (testnet/mainnet)

        Returns:
            List of active wallets
        """
        result = await db.execute(
            select(OstiumWallet).where(
                OstiumWallet.provider_type == provider_type,
                OstiumWallet.network == network,
                OstiumWallet.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_by_provider_and_network(
        self, db: AsyncSession, provider_type: str, network: str
    ) -> list[OstiumWallet]:
        """Get all wallets by provider and network.

        Args:
            db: Database session
            provider_type: Provider type (privy/dynamic)
            network: Network (testnet/mainnet)

        Returns:
            List of wallets
        """
        result = await db.execute(
            select(OstiumWallet).where(
                OstiumWallet.provider_type == provider_type,
                OstiumWallet.network == network,
            )
        )
        return list(result.scalars().all())

    async def deactivate(self, db: AsyncSession, wallet_id: int) -> OstiumWallet | None:
        """Deactivate a wallet.

        Args:
            db: Database session
            wallet_id: Wallet ID

        Returns:
            Updated wallet or None if not found
        """
        wallet = await self.get(db, wallet_id)
        if wallet:
            return await self.update(db, wallet, {"is_active": False})
        return None

    async def activate(self, db: AsyncSession, wallet_id: int) -> OstiumWallet | None:
        """Activate a wallet.

        Args:
            db: Database session
            wallet_id: Wallet ID

        Returns:
            Updated wallet or None if not found
        """
        wallet = await self.get(db, wallet_id)
        if wallet:
            return await self.update(db, wallet, {"is_active": True})
        return None
