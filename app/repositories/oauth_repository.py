"""OAuth connection repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import OAuthConnection
from app.repositories.base import BaseRepository


class OAuthRepository(BaseRepository[OAuthConnection]):
    """OAuth connection repository."""

    def __init__(self) -> None:
        """Initialize OAuth repository."""
        super().__init__(OAuthConnection)

    async def get_by_user_and_provider(
        self, db: AsyncSession, user_id: int, provider: str
    ) -> OAuthConnection | None:
        """Get OAuth connection by user ID and provider."""
        result = await db.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == user_id, OAuthConnection.provider == provider
            )
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_provider_user_id(
        self, db: AsyncSession, provider: str, provider_user_id: str
    ) -> OAuthConnection | None:
        """Get OAuth connection by provider and provider user ID."""
        result = await db.execute(
            select(OAuthConnection).where(
                OAuthConnection.provider == provider,
                OAuthConnection.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()  # type: ignore
