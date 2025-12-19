"""Wallet connection repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import WalletConnection
from app.repositories.base import BaseRepository


class WalletConnectionRepository(BaseRepository[WalletConnection]):
    """Wallet connection repository."""

    def __init__(self) -> None:
        """Initialize wallet connection repository."""
        super().__init__(WalletConnection)

    async def get_by_wallet_address(
        self, db: AsyncSession, wallet_address: str
    ) -> WalletConnection | None:
        """Get wallet connection by wallet address."""
        result = await db.execute(
            select(WalletConnection).where(WalletConnection.wallet_address == wallet_address)
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_primary_by_user(self, db: AsyncSession, user_id: int) -> WalletConnection | None:
        """Get primary wallet connection for user."""
        result = await db.execute(
            select(WalletConnection).where(
                WalletConnection.user_id == user_id,
                WalletConnection.is_primary == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_user(self, db: AsyncSession, user_id: int) -> list[WalletConnection]:
        """Get all wallet connections for user."""
        result = await db.execute(
            select(WalletConnection).where(WalletConnection.user_id == user_id)
        )
        return list(result.scalars().all())
