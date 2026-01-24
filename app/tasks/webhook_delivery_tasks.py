"""Webhook delivery background tasks."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from celery import Task

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETRY_DELAYS = [900, 3600, 21600, 86400]
MAX_RETRIES = 4


class WebhookDeliveryTask(Task):
    """Base task for webhook delivery with retry logic."""

    autoretry_for = (Exception,)
    max_retries = MAX_RETRIES
    retry_backoff = True


@celery_app.task(name="deliver_webhook", bind=True, base=WebhookDeliveryTask)
def deliver_webhook_task(self: Task, delivery_id: str) -> dict[str, Any]:
    """Deliver a webhook with retry logic and auto-disable.

    Retry schedule:
    - Attempt 1: Immediate
    - Attempt 2: 15 minutes later (900s)
    - Attempt 3: 1 hour later (3600s)
    - Attempt 4: 6 hours later (21600s)
    - Attempt 5: 24 hours later (86400s)

    After 4 failures (5 total attempts), the webhook is auto-disabled.

    Args:
        delivery_id: WebhookDelivery ID to deliver

    Returns:
        Delivery result dictionary
    """
    from app.core.database import get_session_maker
    from app.repositories.webhook_repository import (
        WebhookConfigurationRepository,
        WebhookDeliveryRepository,
    )
    from app.services.webhook_service import WebhookService

    async def _deliver() -> dict[str, Any]:
        """Async delivery logic."""
        AsyncSessionLocal = get_session_maker()
        async with AsyncSessionLocal() as db:
            delivery_repo = WebhookDeliveryRepository()
            webhook_repo = WebhookConfigurationRepository()
            webhook_service = WebhookService(db)

            delivery = await delivery_repo.get_by_delivery_id(db, delivery_id)

            if not delivery:
                logger.error(f"Delivery {delivery_id} not found")
                return {"status": "not_found", "delivery_id": delivery_id}

            webhook = await webhook_repo.get(db, delivery.webhook_id)

            if not webhook:
                logger.error(f"Webhook {delivery.webhook_id} not found for delivery {delivery_id}")
                return {"status": "webhook_not_found", "delivery_id": delivery_id}

            if not webhook.is_active:
                logger.info(f"Webhook {webhook.id} is disabled, skipping delivery {delivery_id}")
                return {
                    "status": "webhook_disabled",
                    "delivery_id": delivery_id,
                    "webhook_id": webhook.id,
                }

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    import json

                    payload_dict = json.loads(delivery.payload)
                    signature = webhook_service._generate_hmac(webhook.secret, payload_dict)

                    headers = {
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": f"sha256={signature}",
                        "X-Webhook-Delivery-ID": delivery_id,
                        "X-Webhook-Event-Type": delivery.event_type,
                    }

                    response = await client.post(
                        webhook.url,
                        json=delivery.payload,
                        headers=headers,
                    )

                    delivery.status_code = response.status_code
                    delivery.success = 200 <= response.status_code < 300

                    if delivery.success:
                        webhook.last_delivery_at = datetime.utcnow()
                        await db.commit()
                        logger.info(
                            f"Successfully delivered webhook {delivery_id} to {webhook.url}"
                        )
                        return {
                            "status": "success",
                            "delivery_id": delivery_id,
                            "status_code": response.status_code,
                        }
                    else:
                        delivery.retry_count += 1

                        if delivery.retry_count < MAX_RETRIES:
                            retry_delay = RETRY_DELAYS[delivery.retry_count - 1]
                            delivery.next_retry_at = datetime.utcnow() + timedelta(
                                seconds=retry_delay
                            )
                            await db.commit()
                            logger.warning(
                                f"Webhook delivery {delivery_id} failed with status {response.status_code}. "
                                f"Retry {delivery.retry_count}/{MAX_RETRIES} in {retry_delay}s"
                            )

                            raise self.retry(countdown=retry_delay) from None
                        else:
                            webhook.is_active = False
                            await db.commit()
                            logger.error(
                                f"Webhook {webhook.id} auto-disabled after {MAX_RETRIES} failures"
                            )
                            return {
                                "status": "failed_max_retries",
                                "delivery_id": delivery_id,
                                "webhook_id": webhook.id,
                                "auto_disabled": True,
                            }

            except httpx.RequestError as e:
                delivery.retry_count += 1
                delivery.error_message = str(e)[:500]

                if delivery.retry_count < MAX_RETRIES:
                    retry_delay = RETRY_DELAYS[delivery.retry_count - 1]
                    delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                    await db.commit()
                    logger.warning(
                        f"Webhook delivery {delivery_id} failed with error: {str(e)}. "
                        f"Retry {delivery.retry_count}/{MAX_RETRIES} in {retry_delay}s"
                    )

                    raise self.retry(countdown=retry_delay, exc=e) from None
                else:
                    webhook.is_active = False
                    await db.commit()
                    logger.error(
                        f"Webhook {webhook.id} auto-disabled after {MAX_RETRIES} failures: {str(e)}"
                    )
                    return {
                        "status": "failed_max_retries",
                        "delivery_id": delivery_id,
                        "webhook_id": webhook.id,
                        "error": str(e),
                        "auto_disabled": True,
                    }

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_deliver())
    except Exception as e:
        logger.error(f"Fatal error in deliver_webhook task: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "delivery_id": delivery_id,
            "error": str(e),
        }
