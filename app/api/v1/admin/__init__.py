"""Admin API module."""

from fastapi import APIRouter

from app.api.v1.admin import ostium

router = APIRouter()

router.include_router(ostium.router, prefix="/ostium", tags=["admin-ostium"])
