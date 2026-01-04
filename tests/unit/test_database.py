"""Test database utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.database import Base, close_db, get_db, get_engine, get_session_maker, init_db


class TestDatabase:
    """Test database utilities."""

    def test_get_engine(self):
        """Test getting database engine."""
        with (
            patch("app.core.database.create_async_engine") as mock_create_engine,
            patch("app.core.database.settings") as mock_settings,
        ):
            mock_settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
            mock_settings.DEBUG = False
            mock_settings.DATABASE_POOL_SIZE = 5
            mock_settings.DATABASE_MAX_OVERFLOW = 10
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Reset global engine
            import app.core.database

            app.core.database.engine = None

            engine = get_engine()

            assert engine == mock_engine
            mock_create_engine.assert_called_once()

    def test_get_engine_cached(self):
        """Test getting cached engine."""
        with patch("app.core.database.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Set global engine
            import app.core.database

            app.core.database.engine = mock_engine

            engine = get_engine()

            assert engine == mock_engine
            mock_create_engine.assert_not_called()

    def test_get_session_maker(self):
        """Test getting session maker."""
        with (
            patch("app.core.database.get_engine") as mock_get_engine,
            patch("app.core.database.async_sessionmaker") as mock_sessionmaker,
        ):
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine
            mock_session = MagicMock()
            mock_sessionmaker.return_value = mock_session

            session_maker = get_session_maker()

            assert session_maker == mock_session
            mock_get_engine.assert_called_once()
            mock_sessionmaker.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_success(self):
        """Test getting database session successfully."""
        with patch("app.core.database.get_session_maker") as mock_get_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.close = AsyncMock()

            mock_sessionmaker = MagicMock()
            mock_sessionmaker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sessionmaker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_sessionmaker

            async for session in get_db():
                assert session == mock_session
                # Don't break - let the generator complete to trigger finally block
                pass

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_with_exception(self):
        """Test getting database session with exception."""
        with patch("app.core.database.get_session_maker") as mock_get_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()

            # Create a proper async context manager
            class MockAsyncContextManager:
                def __init__(self, session):
                    self.session = session

                async def __aenter__(self):
                    return self.session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    # The get_db function handles exceptions in its try/except block
                    # So __aexit__ will be called after the exception is handled
                    return False  # Don't suppress the exception

            mock_sessionmaker = MagicMock()
            mock_sessionmaker.return_value = MockAsyncContextManager(mock_session)
            mock_get_session_maker.return_value = mock_sessionmaker

            # Use the generator directly to simulate exception being sent to it
            gen = get_db()
            try:
                _ = await gen.__anext__()
                # Now send an exception to the generator (simulating exception in loop body)
                try:
                    await gen.athrow(Exception("Test error"))
                except StopAsyncIteration:
                    pass
            except Exception as e:
                # Exception should propagate
                assert "Test error" in str(e)

            # The rollback should be called in the except block of get_db
            mock_session.rollback.assert_called_once()
            # close should be called in the finally block
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_db(self):
        """Test initializing database."""
        with patch("app.core.database.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock()

            # Mock the async context manager for begin()
            mock_begin = MagicMock()
            mock_begin.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_begin.__aexit__ = AsyncMock(return_value=None)
            mock_engine.begin = MagicMock(return_value=mock_begin)

            mock_get_engine.return_value = mock_engine

            await init_db()

            mock_conn.run_sync.assert_called_once_with(Base.metadata.create_all)

    @pytest.mark.asyncio
    async def test_close_db_with_engine(self):
        """Test closing database with engine."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()
            import app.core.database

            app.core.database.engine = mock_engine

            await close_db()

            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_without_engine(self):
        """Test closing database without engine."""
        import app.core.database

        app.core.database.engine = None

        await close_db()

        # Should not raise any exception
