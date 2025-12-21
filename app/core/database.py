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


async def init_db(
    initial_retry_delay: float = 2.0,
    max_retry_delay: float = 30.0,
) -> None:
    """Initialize database tables, waiting until database is available.

    This function will retry indefinitely until the database connection succeeds.
    This is useful for containerized deployments where the database might not
    be ready when the application starts.

    Args:
        initial_retry_delay: Initial delay between retries in seconds (exponential backoff)
        max_retry_delay: Maximum delay between retries in seconds (caps exponential backoff)

    Raises:
        RuntimeError: If a non-connection error occurs (e.g., authentication failure)
    """
    attempt = 0
    retry_delay = initial_retry_delay

    # Extract database host for better error messages
    db_host = "configured database"
    if "@" in settings.DATABASE_URL:
        try:
            db_host = settings.DATABASE_URL.split("@")[-1].split("/")[0]
        except Exception:
            pass

    while True:
        attempt += 1
        try:
            logger.info(f"Connecting to database (attempt {attempt})...")
            async with get_engine().begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.success("Database connection established and tables initialized successfully")
            return

        except ConnectionRefusedError:
            logger.warning(
                f"Database connection refused. "
                f"Waiting for PostgreSQL to be available at {db_host}... "
                f"Retrying in {retry_delay:.1f}s (attempt {attempt})"
            )
            await asyncio.sleep(retry_delay)
            # Exponential backoff with max cap
            retry_delay = min(retry_delay * 2, max_retry_delay)

        except Exception as e:
            # Check if error is connection-related
            error_str = str(e).lower()
            is_connection_error = any(
                keyword in error_str
                for keyword in [
                    "connection",
                    "refused",
                    "timeout",
                    "network",
                    "unreachable",
                    "name resolution",
                ]
            )

            if is_connection_error:
                logger.warning(
                    f"Database connection error: {type(e).__name__}: {str(e)}. "
                    f"Waiting for database to be available... "
                    f"Retrying in {retry_delay:.1f}s (attempt {attempt})"
                )
                await asyncio.sleep(retry_delay)
                # Exponential backoff with max cap
                retry_delay = min(retry_delay * 2, max_retry_delay)
            else:
                # Non-connection errors (e.g., authentication, invalid config) should fail immediately
                logger.error(
                    f"Database initialization failed with non-connection error: "
                    f"{type(e).__name__}: {str(e)}"
                )
                raise RuntimeError(
                    f"Database initialization failed: {type(e).__name__}: {str(e)}. "
                    f"Please check your DATABASE_URL configuration."
                ) from e


async def close_db() -> None:
    """Close database connection."""
    if engine is not None:
        await engine.dispose()
