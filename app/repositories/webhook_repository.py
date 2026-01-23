"""Webhook repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookConfiguration, WebhookDelivery
from app.repositories.base import BaseRepository


class WebhookConfigurationRepository(BaseRepository[WebhookConfiguration]):
    """Repository for webhook configuration operations."""

    def __init__(self) -> None:
        """Initialize webhook configuration repository."""
        super().__init__(WebhookConfiguration)

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WebhookConfiguration]:
        """Get webhook configurations by user ID."""
        result = await db.execute(
            select(WebhookConfiguration)
            .where(WebhookConfiguration.user_id == user_id)
            .order_by(WebhookConfiguration.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_event_type(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str,
    ) -> list[WebhookConfiguration]:
        """Get active webhooks for specific event type."""
        result = await db.execute(
            select(WebhookConfiguration).where(
                WebhookConfiguration.user_id == user_id,
                WebhookConfiguration.is_active.is_(True),
            )
        )
        webhooks = list(result.scalars().all())
        return [wh for wh in webhooks if event_type in wh.event_types]

    async def update_last_delivery(
        self,
        db: AsyncSession,
        webhook_id: int,
    ) -> WebhookConfiguration | None:
        """Update last delivery timestamp."""
        from datetime import datetime

        webhook = await self.get(db, webhook_id)
        if webhook:
            webhook.last_delivery_at = datetime.utcnow()
            await db.commit()
            await db.refresh(webhook)
        return webhook

    async def disable_webhook(
        self,
        db: AsyncSession,
        webhook_id: int,
    ) -> WebhookConfiguration | None:
        """Disable webhook configuration."""
        webhook = await self.get(db, webhook_id)
        if webhook:
            webhook.is_active = False
            await db.commit()
            await db.refresh(webhook)
        return webhook


class WebhookDeliveryRepository(BaseRepository[WebhookDelivery]):
    """Repository for webhook delivery operations."""

    def __init__(self) -> None:
        """Initialize webhook delivery repository."""
        super().__init__(WebhookDelivery)

    async def get_by_webhook(
        self,
        db: AsyncSession,
        webhook_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """Get deliveries by webhook ID."""
        result = await db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_delivery_id(
        self,
        db: AsyncSession,
        delivery_id: str,
    ) -> list[WebhookDelivery]:
        """Get all delivery attempts by delivery ID."""
        result = await db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.delivery_id == delivery_id)
            .order_by(WebhookDelivery.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_failures_by_delivery_id(
        self,
        db: AsyncSession,
        delivery_id: str,
    ) -> int:
        """Count failed attempts for a delivery ID."""
        deliveries = await self.get_by_delivery_id(db, delivery_id)
        return sum(1 for d in deliveries if not d.success)

    async def get_recent_failures(
        self,
        db: AsyncSession,
        webhook_id: int,
        limit: int = 10,
    ) -> list[WebhookDelivery]:
        """Get recent failed deliveries for a webhook."""
        result = await db.execute(
            select(WebhookDelivery)
            .where(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.success.is_(False),
            )
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
