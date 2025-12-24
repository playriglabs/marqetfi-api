"""Admin API module."""

from fastapi import APIRouter

from app.api.v1.admin import configuration, ostium, risk

router = APIRouter()

router.include_router(ostium.router, prefix="/ostium", tags=["admin-ostium"])
router.include_router(configuration.router, prefix="/config", tags=["admin-config"])
router.include_router(risk.router, tags=["admin-risk"])
