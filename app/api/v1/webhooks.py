"""Webhook CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.repositories.webhook_repository import (
    WebhookConfigurationRepository,
    WebhookDeliveryRepository,
)
from app.schemas.webhook import (
    WebhookConfigCreate,
    WebhookConfigResponse,
    WebhookConfigUpdate,
    WebhookDeliveryResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/", response_model=WebhookConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookConfigResponse:
    """Create a new webhook configuration."""
    repo = WebhookConfigurationRepository()
    webhook = await repo.create(
        db,
        {
            "user_id": current_user.id,
            "url": str(webhook_data.url),
            "secret": webhook_data.secret,
            "event_types": webhook_data.event_types,
            "is_active": True,
        },
    )
    return WebhookConfigResponse.model_validate(webhook)


@router.get("/", response_model=list[WebhookConfigResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[WebhookConfigResponse]:
    """List all webhooks for the current user."""
    repo = WebhookConfigurationRepository()
    webhooks = await repo.get_by_user(db, current_user.id, skip, limit)
    return [WebhookConfigResponse.model_validate(w) for w in webhooks]


@router.get("/{webhook_id}", response_model=WebhookConfigResponse)
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookConfigResponse:
    """Get a single webhook by ID."""
    repo = WebhookConfigurationRepository()
    webhook = await repo.get(db, webhook_id)

    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this webhook",
        )

    return WebhookConfigResponse.model_validate(webhook)


@router.put("/{webhook_id}", response_model=WebhookConfigResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookConfigResponse:
    """Update a webhook configuration."""
    repo = WebhookConfigurationRepository()
    webhook = await repo.get(db, webhook_id)

    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    update_data = webhook_data.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    updated = await repo.update(db, webhook, update_data)
    return WebhookConfigResponse.model_validate(updated)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a webhook configuration."""
    repo = WebhookConfigurationRepository()
    webhook = await repo.get(db, webhook_id)

    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    await repo.delete(db, webhook_id)


@router.put("/{webhook_id}/enable", response_model=WebhookConfigResponse)
async def enable_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookConfigResponse:
    """Re-enable a disabled webhook."""
    repo = WebhookConfigurationRepository()
    webhook = await repo.get(db, webhook_id)

    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    webhook.is_active = True
    await db.commit()
    await db.refresh(webhook)
    return WebhookConfigResponse.model_validate(webhook)


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[WebhookDeliveryResponse]:
    """Get delivery history for a webhook."""
    webhook_repo = WebhookConfigurationRepository()
    webhook = await webhook_repo.get(db, webhook_id)

    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    delivery_repo = WebhookDeliveryRepository()
    deliveries = await delivery_repo.get_by_webhook(db, webhook_id, skip, limit)
    return [WebhookDeliveryResponse.model_validate(d) for d in deliveries]
