"""Webhook handlers."""

from fastapi import APIRouter

from app.api.v1.webhooks import example

router = APIRouter()

router.include_router(example.router, prefix="/example", tags=["webhooks-example"])

