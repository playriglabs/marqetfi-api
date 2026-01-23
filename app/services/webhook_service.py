"""Webhook service for event delivery."""

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.repositories.webhook_repository import (
    WebhookConfigurationRepository,
    WebhookDeliveryRepository,
)


class WebhookService:
    """Service for webhook event delivery with HMAC signatures and retry logic."""

    MAX_RETRY_ATTEMPTS = 4
    RETRY_DELAYS = [1, 5, 15, 60]

    def __init__(self, db: AsyncSession):
        """Initialize webhook service.

        Args:
            db: Database session
        """
        self.db = db
        self.webhook_repo = WebhookConfigurationRepository()
        self.delivery_repo = WebhookDeliveryRepository()
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def send_webhook(
        self,
        user_id: int,
        event_type: str,
        event_data: dict[str, Any],
    ) -> None:
        """Send webhook to all active subscribers for event type.

        Args:
            user_id: User ID who triggered the event
            event_type: Event type (e.g., 'order.created', 'position.updated')
            event_data: Event payload data
        """
        webhooks = await self.webhook_repo.get_active_by_event_type(self.db, user_id, event_type)

        if not webhooks:
            logger.debug(f"No active webhooks for user {user_id}, event {event_type}")
            return

        for webhook in webhooks:
            delivery_id = str(uuid.uuid4())
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data,
            }

            signature = self._generate_hmac(webhook.secret, payload)

            delivery = await self.delivery_repo.create(
                self.db,
                {
                    "webhook_id": webhook.id,
                    "delivery_id": delivery_id,
                    "event_type": event_type,
                    "payload": json.dumps(payload),
                    "success": False,
                    "retry_count": 0,
                },
            )

            asyncio.create_task(
                self._deliver_with_retry(
                    delivery.id,
                    webhook.id,
                    str(webhook.url),
                    payload,
                    signature,
                    delivery_id,
                )
            )

    async def _deliver_with_retry(
        self,
        delivery_id: int,
        webhook_id: int,
        url: str,
        payload: dict[str, Any],
        signature: str,
        delivery_uuid: str,
    ) -> None:
        """Deliver webhook with retry logic and auto-disable on failures.

        Args:
            delivery_id: Delivery record ID
            webhook_id: Webhook configuration ID
            url: Webhook URL
            payload: Event payload
            signature: HMAC signature
            delivery_uuid: Unique delivery UUID for tracking retries
        """
        for attempt in range(self.MAX_RETRY_ATTEMPTS):
            try:
                response = await self.http_client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Delivery-ID": delivery_uuid,
                    },
                )

                delivery = await self.delivery_repo.get(self.db, delivery_id)
                if delivery:
                    delivery.status_code = response.status_code
                    delivery.error_message = response.text if response.status_code >= 400 else None
                    delivery.retry_count = attempt + 1

                    if response.status_code in {200, 201, 202, 204}:
                        delivery.success = True
                        await self.db.commit()
                        await self.webhook_repo.update_last_delivery(self.db, webhook_id)
                        logger.info(
                            f"Webhook delivered: {webhook_id}, delivery: {delivery_uuid}, "
                            f"attempt: {attempt + 1}"
                        )
                        return
                    else:
                        delivery.success = False
                        await self.db.commit()
                        logger.warning(
                            f"Webhook failed with status {response.status_code}: "
                            f"{webhook_id}, attempt: {attempt + 1}"
                        )

            except httpx.TimeoutException:
                logger.error(f"Webhook timeout: {webhook_id}, attempt: {attempt + 1}")
                delivery = await self.delivery_repo.get(self.db, delivery_id)
                if delivery:
                    delivery.retry_count = attempt + 1
                    delivery.success = False
                    delivery.error_message = "Timeout"
                    await self.db.commit()

            except Exception as e:
                logger.error(f"Webhook error: {webhook_id}, attempt: {attempt + 1}, error: {e}")
                delivery = await self.delivery_repo.get(self.db, delivery_id)
                if delivery:
                    delivery.retry_count = attempt + 1
                    delivery.success = False
                    delivery.error_message = str(e)
                    await self.db.commit()

            if attempt < self.MAX_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(self.RETRY_DELAYS[attempt])

        failure_count = await self.delivery_repo.count_failures_by_delivery_id(
            self.db, delivery_uuid
        )

        if failure_count >= self.MAX_RETRY_ATTEMPTS:
            await self.webhook_repo.disable_webhook(self.db, webhook_id)
            logger.warning(
                f"Webhook auto-disabled after {self.MAX_RETRY_ATTEMPTS} failures: {webhook_id}"
            )

    def _generate_hmac(self, secret: str, payload: dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for webhook payload.

        Args:
            secret: Webhook secret key
            payload: Event payload dict

        Returns:
            Hex-encoded HMAC signature
        """
        message = json.dumps(payload, sort_keys=True)
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def verify_webhook_signature(
        self,
        secret: str,
        payload: dict[str, Any],
        signature: str,
    ) -> bool:
        """Verify webhook HMAC signature.

        Args:
            secret: Webhook secret key
            payload: Event payload dict
            signature: Received signature to verify

        Returns:
            True if signature is valid
        """
        expected_signature = self._generate_hmac(secret, payload)
        return hmac.compare_digest(expected_signature, signature)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
