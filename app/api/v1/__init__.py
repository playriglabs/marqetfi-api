"""API v1 module."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, health, prices, trading, users
from app.api.v1.auth import oauth, wallet
from app.api.v1.webhooks import router as webhooks_router

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(oauth.router, prefix="/auth/oauth", tags=["oauth"])
router.include_router(wallet.router, prefix="/auth/wallet", tags=["wallet"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
router.include_router(trading.router, prefix="/trading", tags=["trading"])
router.include_router(prices.router, prefix="/prices", tags=["prices"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
