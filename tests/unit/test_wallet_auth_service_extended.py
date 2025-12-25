"""Extended tests for WalletAuthService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from web3 import Web3

from app.models.auth import WalletConnection
from app.models.enums import WalletType
from app.models.user import User
from app.services.wallet_auth_service import WalletAuthService

w3 = Web3()


class TestWalletAuthServiceExtended:
    """Extended tests for WalletAuthService class."""

    @pytest.fixture
    def wallet_auth_service(self):
        """Create WalletAuthService instance."""
        return WalletAuthService()

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_link_wallet_to_user_new(self, wallet_auth_service, db_session, sample_user):
        """Test linking new wallet to user."""
        with (
            patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute,
            patch("app.services.wallet_auth_service.cache_manager") as mock_cache,
        ):
            # Mock no existing connection
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            mock_cache.get = AsyncMock(return_value=None)

            wallet_conn = await wallet_auth_service.link_wallet_to_user(
                db=db_session,
                user=sample_user,
                wallet_address="0x1234567890123456789012345678901234567890",
                wallet_type=WalletType.MPC,
                provider="privy",
                provider_wallet_id="wallet_123",
            )

            assert wallet_conn is not None

    @pytest.mark.asyncio
    async def test_get_user_wallet_connections(self, wallet_auth_service, db_session, sample_user):
        """Test getting user wallet connections."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.id = 1
        mock_conn.wallet_address = "0x123"
        mock_conn.wallet_type = WalletType.EXTERNAL
        mock_conn.provider = "metamask"
        mock_conn.provider_wallet_id = None
        mock_conn.is_primary = True
        mock_conn.verified = True
        mock_conn.verified_at = None
        mock_conn.last_used_at = None
        mock_conn.created_at = None

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_conn]
            mock_execute.return_value = mock_result

            connections = await wallet_auth_service.get_user_wallet_connections(
                db=db_session, user=sample_user
            )

            assert len(connections) == 1
            assert connections[0].wallet_address == "0x123"

    @pytest.mark.asyncio
    async def test_connect_wallet_existing_connection(
        self, wallet_auth_service, db_session, sample_user
    ):
        """Test connecting wallet when connection already exists."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.user_id = 1
        mock_conn.verified = False

        with (
            patch("app.services.wallet_auth_service.cache_manager") as mock_cache,
            patch(
                "app.services.wallet_auth_service.w3.eth.account.recover_message",
                return_value="0x1234567890123456789012345678901234567890",
            ),
            patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute,
            patch.object(db_session, "commit", new_callable=AsyncMock),
            patch.object(db_session, "refresh", new_callable=AsyncMock),
        ):
            mock_cache.get = AsyncMock(return_value="nonce123")
            mock_cache.delete = AsyncMock()

            # Mock existing connection
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_conn
            mock_execute.return_value = mock_result

            wallet_conn = await wallet_auth_service.connect_wallet(
                db=db_session,
                user=sample_user,
                wallet_address="0x1234567890123456789012345678901234567890",
                signature="0xsig",
                nonce="nonce123",
            )

            assert wallet_conn is not None

    @pytest.mark.asyncio
    async def test_connect_wallet_wrong_user(self, wallet_auth_service, db_session, sample_user):
        """Test connecting wallet that belongs to another user."""
        mock_conn = MagicMock(spec=WalletConnection)
        mock_conn.user_id = 999  # Different user

        with (
            patch("app.services.wallet_auth_service.cache_manager") as mock_cache,
            patch(
                "app.services.wallet_auth_service.w3.eth.account.recover_message",
                return_value="0x1234567890123456789012345678901234567890",
            ),
            patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute,
        ):
            mock_cache.get = AsyncMock(return_value="nonce123")

            # Mock existing connection for different user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_conn
            mock_execute.return_value = mock_result

            with pytest.raises(ValueError, match="Wallet is already connected to another account"):
                await wallet_auth_service.connect_wallet(
                    db=db_session,
                    user=sample_user,
                    wallet_address="0x1234567890123456789012345678901234567890",
                    signature="0xsig",
                    nonce="nonce123",
                )

    @pytest.mark.asyncio
    async def test_create_mpc_wallet_existing_wallet(
        self, wallet_auth_service, db_session, sample_user
    ):
        """Test creating MPC wallet when wallet already exists."""
        from app.models.wallet import Wallet

        mock_wallet = MagicMock(spec=Wallet)
        mock_wallet.id = 1
        mock_wallet.user_id = 1
        mock_wallet.provider_type = "privy"
        mock_wallet.provider_wallet_id = "wallet_123"

        with (
            patch("app.services.wallet_auth_service.WalletProviderFactory") as mock_factory,
            patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute,
            patch.object(db_session, "commit", new_callable=AsyncMock),
            patch.object(db_session, "refresh", new_callable=AsyncMock),
        ):
            mock_provider = MagicMock()
            mock_provider.create_wallet = AsyncMock(
                return_value={"wallet_id": "wallet_123", "address": "0x123"}
            )
            mock_provider.initialize = AsyncMock()
            mock_factory.get_provider = AsyncMock(return_value=mock_provider)

            # Mock existing wallet
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_wallet
            mock_execute.return_value = mock_result

            with patch("app.services.wallet_auth_service.WalletRepository") as mock_repo:
                result = await wallet_auth_service.create_mpc_wallet(
                    db=db_session, user=sample_user, provider="privy", network="mainnet"
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_create_mpc_wallet_unsupported_provider(
        self, wallet_auth_service, db_session, sample_user
    ):
        """Test creating MPC wallet with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            await wallet_auth_service.create_mpc_wallet(
                db=db_session, user=sample_user, provider="invalid", network="mainnet"
            )
