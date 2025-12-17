"""Example webhook handler."""

from fastapi import APIRouter, Header, HTTPException, Request, status
from loguru import logger

router = APIRouter()


@router.post("")
async def handle_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
) -> dict:
    """Handle example webhook.

    Args:
        request: FastAPI request object
        x_webhook_signature: Webhook signature for verification

    Returns:
        Success response

    Raises:
        HTTPException: If signature verification fails
    """
    # Verify signature (implement your verification logic)
    if x_webhook_signature:
        # TODO: Implement signature verification
        # if not verify_signature(body, x_webhook_signature):
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid webhook signature",
        #     )
        pass

    # Parse payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from e

    # Process webhook
    logger.info(f"Received webhook: {payload}")

    # TODO: Add your webhook processing logic here
    # Example: Queue background task
    # from app.tasks.example_tasks import example_task
    # example_task.delay(payload)

    return {"status": "received", "message": "Webhook processed successfully"}
