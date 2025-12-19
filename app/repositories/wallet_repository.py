"""Wallet repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    """Wallet repository."""

    def __init__(self) -> None:
        """Initialize wallet repository."""
        super().__init__(Wallet)

    async def get_by_wallet_address(self, db: AsyncSession, wallet_address: str) -> Wallet | None:
        """Get wallet by wallet address."""
        result = await db.execute(select(Wallet).where(Wallet.wallet_address == wallet_address))
        return result.scalar_one_or_none()  # type: ignore

    async def get_primary_by_user(self, db: AsyncSession, user_id: int) -> Wallet | None:
        """Get primary wallet for user."""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id, Wallet.is_primary == True)  # noqa: E712
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_user(self, db: AsyncSession, user_id: int) -> list[Wallet]:
        """Get all wallets for user."""
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_provider_wallet_id(
        self, db: AsyncSession, provider_type: str, provider_wallet_id: str
    ) -> Wallet | None:
        """Get wallet by provider type and provider wallet ID."""
        result = await db.execute(
            select(Wallet).where(
                Wallet.provider_type == provider_type,
                Wallet.provider_wallet_id == provider_wallet_id,
            )
        )
        return result.scalar_one_or_none()  # type: ignore
