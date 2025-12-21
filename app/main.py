"""Main application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1 import router as api_v1_router
from app.config import get_settings
from app.core.cache import cache_manager
from app.core.database import close_db, init_db
from app.core.logging import setup_logging
from app.middleware.error_handler import error_handler_middleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan manager."""
    # Startup
    setup_logging()

    # Wait for database to be available before starting the application
    logger.info("Waiting for database to be available...")
    await init_db()

    # Initialize cache (also with graceful handling if needed)
    try:
        await cache_manager.connect()
    except Exception as e:
        logger.warning(f"Cache connection failed: {e}. Application will continue without cache.")

    yield

    # Shutdown
    try:
        await cache_manager.disconnect()
    except Exception:
        pass  # Ignore errors during shutdown

    try:
        await close_db()
    except Exception:
        pass  # Ignore errors during shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Custom middleware
app.middleware("http")(error_handler_middleware)

# Include routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": settings.DOCS_URL,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
