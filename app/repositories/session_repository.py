"""Session repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Session repository."""

    def __init__(self) -> None:
        """Initialize session repository."""
        super().__init__(Session)

    async def get_by_token_hash(self, db: AsyncSession, token_hash: str) -> Session | None:
        """Get session by token hash."""
        result = await db.execute(select(Session).where(Session.token_hash == token_hash))
        return result.scalar_one_or_none()  # type: ignore

    async def get_by_refresh_token_hash(
        self, db: AsyncSession, refresh_token_hash: str
    ) -> Session | None:
        """Get session by refresh token hash."""
        result = await db.execute(
            select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        )
        return result.scalar_one_or_none()  # type: ignore

    async def get_active_by_user(self, db: AsyncSession, user_id: int) -> list[Session]:
        """Get all active sessions for user."""
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.revoked == False,  # noqa: E712
                Session.expires_at > datetime.utcnow(),
            )
        )
        return list(result.scalars().all())

    async def revoke_session(self, db: AsyncSession, session_id: int) -> bool:
        """Revoke a session."""
        session = await self.get(db, session_id)
        if session:
            session.revoked = True
            session.revoked_at = datetime.utcnow()
            await db.commit()
            await db.refresh(session)
            return True
        return False
