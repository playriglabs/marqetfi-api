"""Deposit repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deposit import Deposit, TokenSwap
from app.repositories.base import BaseRepository


class DepositRepository(BaseRepository[Deposit]):
    """Repository for deposit operations."""

    def __init__(self) -> None:
        """Initialize deposit repository."""
        super().__init__(Deposit)

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Deposit]:
        """Get deposits by user ID."""
        result = await db.execute(
            select(Deposit)
            .where(Deposit.user_id == user_id)
            .order_by(Deposit.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Deposit]:
        """Get deposits by status."""
        result = await db.execute(
            select(Deposit)
            .where(Deposit.status == status)
            .order_by(Deposit.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_provider(
        self,
        db: AsyncSession,
        provider: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Deposit]:
        """Get deposits by provider."""
        result = await db.execute(
            select(Deposit)
            .where(Deposit.provider == provider)
            .order_by(Deposit.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_transaction_hash(
        self, db: AsyncSession, transaction_hash: str
    ) -> Deposit | None:
        """Get deposit by transaction hash."""
        result = await db.execute(
            select(Deposit).where(Deposit.transaction_hash == transaction_hash)
        )
        return result.scalar_one_or_none()


class TokenSwapRepository(BaseRepository[TokenSwap]):
    """Repository for token swap operations."""

    def __init__(self) -> None:
        """Initialize token swap repository."""
        super().__init__(TokenSwap)

    async def get_by_deposit(self, db: AsyncSession, deposit_id: int) -> list[TokenSwap]:
        """Get swaps by deposit ID."""
        result = await db.execute(
            select(TokenSwap)
            .where(TokenSwap.deposit_id == deposit_id)
            .order_by(TokenSwap.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TokenSwap]:
        """Get swaps by status."""
        result = await db.execute(
            select(TokenSwap)
            .where(TokenSwap.swap_status == status)
            .order_by(TokenSwap.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_transaction_hash(
        self, db: AsyncSession, transaction_hash: str
    ) -> TokenSwap | None:
        """Get swap by transaction hash."""
        result = await db.execute(
            select(TokenSwap).where(TokenSwap.swap_transaction_hash == transaction_hash)
        )
        return result.scalar_one_or_none()
