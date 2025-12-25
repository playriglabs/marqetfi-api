"""Additional repository tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.auth import Session, WalletConnection
from app.models.provider import OstiumWallet
from app.repositories.ostium_wallet_repository import OstiumWalletRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.wallet_connection_repository import WalletConnectionRepository


class TestOstiumWalletRepository:
    """Test OstiumWalletRepository class."""

    @pytest.fixture
    def wallet_repo(self):
        """Create OstiumWalletRepository instance."""
        return OstiumWalletRepository()

    @pytest.mark.asyncio
    async def test_get_by_provider_wallet_id_success(self, wallet_repo, db_session):
        """Test getting wallet by provider wallet ID."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1
        mock_wallet.provider_wallet_id = "wallet_123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_wallet
            mock_execute.return_value = mock_result

            wallet = await wallet_repo.get_by_provider_wallet_id(db_session, "wallet_123")

            assert wallet is not None
            assert wallet.provider_wallet_id == "wallet_123"

    @pytest.mark.asyncio
    async def test_get_by_address_success(self, wallet_repo, db_session):
        """Test getting wallet by address."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1
        mock_wallet.wallet_address = "0x123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_wallet
            mock_execute.return_value = mock_result

            wallet = await wallet_repo.get_by_address(db_session, "0x123")

            assert wallet is not None

    @pytest.mark.asyncio
    async def test_get_active_by_provider_success(self, wallet_repo, db_session):
        """Test getting active wallets by provider."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_wallet]
            mock_execute.return_value = mock_result

            wallets = await wallet_repo.get_active_by_provider(db_session, "privy", "mainnet")

            assert len(wallets) == 1

    @pytest.mark.asyncio
    async def test_get_by_provider_and_network_success(self, wallet_repo, db_session):
        """Test getting wallets by provider and network."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_wallet]
            mock_execute.return_value = mock_result

            wallets = await wallet_repo.get_by_provider_and_network(db_session, "privy", "mainnet")

            assert len(wallets) == 1

    @pytest.mark.asyncio
    async def test_deactivate_success(self, wallet_repo, db_session):
        """Test deactivating wallet."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1
        mock_wallet.is_active = True

        with patch.object(wallet_repo, "get", new_callable=AsyncMock, return_value=mock_wallet), patch.object(
            wallet_repo, "update", new_callable=AsyncMock, return_value=mock_wallet
        ):
            result = await wallet_repo.deactivate(db_session, wallet_id=1)

            assert result is not None

    @pytest.mark.asyncio
    async def test_activate_success(self, wallet_repo, db_session):
        """Test activating wallet."""
        mock_wallet = MagicMock(spec=OstiumWallet)
        mock_wallet.id = 1
        mock_wallet.is_active = False

        with patch.object(wallet_repo, "get", new_callable=AsyncMock, return_value=mock_wallet), patch.object(
            wallet_repo, "update", new_callable=AsyncMock, return_value=mock_wallet
        ):
            result = await wallet_repo.activate(db_session, wallet_id=1)

            assert result is not None


class TestWalletConnectionRepository:
    """Test WalletConnectionRepository class."""

    @pytest.fixture
    def wallet_conn_repo(self):
        """Create WalletConnectionRepository instance."""
        return WalletConnectionRepository()

    @pytest.mark.asyncio
    async def test_get_by_wallet_address_success(self, wallet_conn_repo, db_session):
        """Test getting wallet connection by address."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.id = 1
        mock_conn.wallet_address = "0x123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_conn
            mock_execute.return_value = mock_result

            conn = await wallet_conn_repo.get_by_wallet_address(db_session, "0x123")

            assert conn is not None

    @pytest.mark.asyncio
    async def test_get_primary_by_user_success(self, wallet_conn_repo, db_session):
        """Test getting primary wallet connection for user."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.id = 1
        mock_conn.user_id = 1
        mock_conn.is_primary = True

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_conn
            mock_execute.return_value = mock_result

            conn = await wallet_conn_repo.get_primary_by_user(db_session, user_id=1)

            assert conn is not None
            assert conn.is_primary is True

    @pytest.mark.asyncio
    async def test_get_by_user_success(self, wallet_conn_repo, db_session):
        """Test getting all wallet connections for user."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.id = 1
        mock_conn.user_id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_conn]
            mock_execute.return_value = mock_result

            conns = await wallet_conn_repo.get_by_user(db_session, user_id=1)

            assert len(conns) == 1


class TestSessionRepository:
    """Test SessionRepository class."""

    @pytest.fixture
    def session_repo(self):
        """Create SessionRepository instance."""
        return SessionRepository()

    @pytest.mark.asyncio
    async def test_get_by_token_hash_success(self, session_repo, db_session):
        """Test getting session by token hash."""
        mock_session = MagicMock(spec=Session)
        mock_session.id = 1
        mock_session.token_hash = "hash123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result

            session = await session_repo.get_by_token_hash(db_session, "hash123")

            assert session is not None

    @pytest.mark.asyncio
    async def test_get_by_refresh_token_hash_success(self, session_repo, db_session):
        """Test getting session by refresh token hash."""
        mock_session = MagicMock(spec=Session)
        mock_session.id = 1
        mock_session.refresh_token_hash = "refresh_hash123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result

            session = await session_repo.get_by_refresh_token_hash(db_session, "refresh_hash123")

            assert session is not None

    @pytest.mark.asyncio
    async def test_get_active_by_user_success(self, session_repo, db_session):
        """Test getting active sessions for user."""
        mock_session = MagicMock(spec=Session)
        mock_session.id = 1
        mock_session.user_id = 1
        mock_session.revoked = False

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_session]
            mock_execute.return_value = mock_result

            sessions = await session_repo.get_active_by_user(db_session, user_id=1)

            assert len(sessions) == 1

    @pytest.mark.asyncio
    async def test_revoke_session_success(self, session_repo, db_session):
        """Test revoking session."""
        mock_session = MagicMock(spec=Session)
        mock_session.id = 1
        mock_session.revoked = False

        with patch.object(session_repo, "get", new_callable=AsyncMock, return_value=mock_session), patch.object(
            db_session, "commit", new_callable=AsyncMock
        ), patch.object(db_session, "refresh", new_callable=AsyncMock):
            result = await session_repo.revoke_session(db_session, session_id=1)

            assert result is True
            assert mock_session.revoked is True

    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self, session_repo, db_session):
        """Test revoking session when not found."""
        with patch.object(session_repo, "get", new_callable=AsyncMock, return_value=None):
            result = await session_repo.revoke_session(db_session, session_id=999)

            assert result is False

