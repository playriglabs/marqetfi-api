"""Database connection and session management."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# Lazy initialization to prevent connection on import
engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create database engine."""
    global engine
    if engine is None:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )
    return engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get session maker."""
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Get database session."""
    AsyncSessionLocal = get_session_maker()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    retries = 5
    delay = 2.0

    for attempt in range(retries):
        try:
            async with get_engine().begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Failed to initialize database after {retries} attempts: {e}")
                raise

            logger.warning(
                f"Database connection attempt {attempt + 1}/{retries} failed. "
                f"Retrying in {delay}s... Error: {e}"
            )
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff


async def close_db() -> None:
    """Close database connection."""
    if engine is not None:
        await engine.dispose()
