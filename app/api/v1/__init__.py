"""API v1 module."""

from fastapi import APIRouter

from app.api.v1 import auth, health, users
from app.api.v1.webhooks import router as webhooks_router

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

