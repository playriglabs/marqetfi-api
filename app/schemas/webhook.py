"""Webhook schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class WebhookConfigCreate(BaseModel):
    """Schema for creating a webhook configuration."""

    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    secret: str = Field(..., description="HMAC secret key", min_length=16, max_length=255)
    event_types: list[str] = Field(..., description="Event types to subscribe to", min_length=1)


class WebhookConfigUpdate(BaseModel):
    """Schema for updating a webhook configuration."""

    url: HttpUrl | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None


class WebhookConfigResponse(BaseModel):
    """Schema for webhook configuration response."""

    id: int
    url: str
    event_types: list[str]
    is_active: bool
    last_delivery_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""

    id: int
    webhook_id: int
    delivery_id: str
    event_type: str
    status_code: int | None
    success: bool
    retry_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
