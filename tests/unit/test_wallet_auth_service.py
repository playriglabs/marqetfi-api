"""Test WalletAuthService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from eth_account import Account
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import WalletConnection
from app.models.enums import WalletType
from app.models.user import User
from app.services.wallet_auth_service import WalletAuthService


class TestWalletAuthService:
    """Test WalletAuthService class."""

    @pytest.fixture
    def service(self):
        """Create WalletAuthService instance."""
        return WalletAuthService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            wallet_type=WalletType.NONE,
        )
        return user

    @pytest.fixture
    def wallet_account(self):
        """Create a test wallet account."""
        return Account.create()

    @pytest.mark.asyncio
    async def test_generate_nonce(self, service):
        """Test nonce generation."""
        wallet_address = "0x1234567890123456789012345678901234567890"

        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)

            nonce = await service.generate_nonce(wallet_address)

            assert nonce is not None
            assert len(nonce) > 0
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == f"wallet_nonce:{wallet_address.lower()}"
            assert call_args[0][1] == nonce
            assert call_args[1]["expire"] == 300

    @pytest.mark.asyncio
    async def test_verify_wallet_signature_valid(self, service, wallet_account):
        """Test valid wallet signature verification."""
        from eth_account.messages import encode_defunct

        message = "Test message"
        message_encoded = encode_defunct(text=message)

        # Sign message
        signed = wallet_account.sign_message(message_encoded)
        signature = signed.signature.hex()

        result = await service.verify_wallet_signature(
            wallet_address=wallet_account.address,
            signature=signature,
            message=message,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_wallet_signature_invalid(self, service, wallet_account):
        """Test invalid wallet signature verification."""
        from eth_account.messages import encode_defunct

        message = "Test message"
        wrong_address = "0x0000000000000000000000000000000000000001"
        message_encoded = encode_defunct(text=message)

        # Sign message
        signed = wallet_account.sign_message(message_encoded)
        signature = signed.signature.hex()

        result = await service.verify_wallet_signature(
            wallet_address=wrong_address,
            signature=signature,
            message=message,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_wallet_signature_exception(self, service):
        """Test signature verification with exception."""
        result = await service.verify_wallet_signature(
            wallet_address="invalid",
            signature="invalid",
            message="test",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_connect_wallet_success(self, service, mock_db, sample_user, wallet_account):
        """Test successful wallet connection."""
        from eth_account.messages import encode_defunct

        wallet_address = wallet_account.address
        nonce = "test_nonce_123"
        message = f"Sign this message to connect your wallet:\n\nNonce: {nonce}"
        message_encoded = encode_defunct(text=message)
        signed = wallet_account.sign_message(message_encoded)
        signature = signed.signature.hex()

        # Mock cache
        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=nonce)
            mock_cache.delete = AsyncMock(return_value=True)

            # Mock database query - no existing connection
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none = MagicMock(return_value=None)
            mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

            # Mock refresh to set ID
            def set_id(obj):
                obj.id = 1

            mock_db.refresh = AsyncMock(side_effect=set_id)

            result = await service.connect_wallet(
                db=mock_db,
                user=sample_user,
                wallet_address=wallet_address,
                signature=signature,
                nonce=nonce,
                provider="metamask",
            )

            assert result is not None
            assert result.wallet_address == wallet_address
            assert result.verified is True
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_wallet_invalid_nonce(self, service, mock_db, sample_user):
        """Test wallet connection with invalid nonce."""
        wallet_address = "0x1234567890123456789012345678901234567890"

        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)  # Nonce not found

            with pytest.raises(ValueError, match="Invalid or expired nonce"):
                await service.connect_wallet(
                    db=mock_db,
                    user=sample_user,
                    wallet_address=wallet_address,
                    signature="0x123",
                    nonce="wrong_nonce",
                )

    @pytest.mark.asyncio
    async def test_connect_wallet_invalid_signature(
        self, service, mock_db, sample_user, wallet_account
    ):
        """Test wallet connection with invalid signature."""
        wallet_address = wallet_account.address
        nonce = "test_nonce_123"

        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=nonce)

            with pytest.raises(ValueError, match="Invalid signature"):
                await service.connect_wallet(
                    db=mock_db,
                    user=sample_user,
                    wallet_address=wallet_address,
                    signature="0xinvalid",
                    nonce=nonce,
                )

    @pytest.mark.asyncio
    async def test_connect_wallet_existing_connection(
        self, service, mock_db, sample_user, wallet_account
    ):
        """Test wallet connection when connection already exists."""
        from eth_account.messages import encode_defunct

        wallet_address = wallet_account.address
        nonce = "test_nonce_123"
        message = f"Sign this message to connect your wallet:\n\nNonce: {nonce}"
        message_encoded = encode_defunct(text=message)
        signed = wallet_account.sign_message(message_encoded)
        signature = signed.signature.hex()

        # Create existing connection
        existing_conn = WalletConnection(
            id=1,
            user_id=sample_user.id,
            wallet_address=wallet_address,
            verified=False,
        )

        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=nonce)
            mock_cache.delete = AsyncMock(return_value=True)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=existing_conn)
            mock_db.execute = AsyncMock(return_value=mock_result)

            def set_id(obj):
                if not hasattr(obj, "id"):
                    obj.id = 1

            mock_db.refresh = AsyncMock(side_effect=set_id)

            result = await service.connect_wallet(
                db=mock_db,
                user=sample_user,
                wallet_address=wallet_address,
                signature=signature,
                nonce=nonce,
            )

            assert result.verified is True
            assert result.verified_at is not None

    @pytest.mark.asyncio
    async def test_connect_wallet_wrong_user(self, service, mock_db, sample_user, wallet_account):
        """Test wallet connection when wallet belongs to another user."""
        from eth_account.messages import encode_defunct

        wallet_address = wallet_account.address
        nonce = "test_nonce_123"
        message = f"Sign this message to connect your wallet:\n\nNonce: {nonce}"
        message_encoded = encode_defunct(text=message)
        signed = wallet_account.sign_message(message_encoded)
        signature = signed.signature.hex()

        # Create existing connection for different user
        existing_conn = WalletConnection(
            id=1,
            user_id=999,  # Different user
            wallet_address=wallet_address,
            verified=True,
        )

        with patch("app.services.wallet_auth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=nonce)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=existing_conn)
            mock_db.execute = AsyncMock(return_value=mock_result)

            with pytest.raises(ValueError, match="Wallet is already connected to another account"):
                await service.connect_wallet(
                    db=mock_db,
                    user=sample_user,
                    wallet_address=wallet_address,
                    signature=signature,
                    nonce=nonce,
                )

    @pytest.mark.asyncio
    async def test_create_mpc_wallet_success(self, service, mock_db, sample_user):
        """Test successful MPC wallet creation."""
        wallet_data = {
            "wallet_id": "privy_wallet_123",
            "address": "0x1234567890123456789012345678901234567890",
            "network": "mainnet",
            "metadata": {"key": "value"},
        }

        with patch("app.services.wallet_auth_service.WalletProviderFactory") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.create_wallet = AsyncMock(return_value=wallet_data)
            mock_provider.initialize = AsyncMock()
            mock_factory.get_provider = AsyncMock(return_value=mock_provider)

            # Mock database queries
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none = MagicMock(return_value=None)  # No existing wallet
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none = MagicMock(return_value=None)  # No primary wallet
            mock_result3 = MagicMock()
            mock_result3.scalar_one_or_none = MagicMock(return_value=None)  # No existing connection
            mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2, mock_result3])

            # Mock wallet repository
            with patch("app.services.wallet_auth_service.WalletRepository") as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_wallet = MagicMock()
                mock_wallet.id = 1
                mock_wallet.is_primary = True
                mock_wallet.user_id = sample_user.id
                mock_repo_instance.create = AsyncMock(return_value=mock_wallet)
                mock_repo_class.return_value = mock_repo_instance

                # Mock link_wallet_to_user to return a connection
                mock_conn = MagicMock()
                mock_conn.id = 1
                with patch.object(
                    service, "link_wallet_to_user", return_value=mock_conn
                ) as mock_link:

                    def refresh_side_effect(obj):
                        if not hasattr(obj, "id"):
                            obj.id = 1

                    mock_db.refresh = AsyncMock(side_effect=refresh_side_effect)

                    result = await service.create_mpc_wallet(
                        db=mock_db, user=sample_user, provider="privy", network="mainnet"
                    )

                    assert result["wallet_id"] == 1
                    assert result["address"] == wallet_data["address"]
                    assert result["provider"] == "privy"
                    mock_link.assert_called_once()
                    mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_mpc_wallet_invalid_provider(self, service, mock_db, sample_user):
        """Test MPC wallet creation with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            await service.create_mpc_wallet(
                db=mock_db, user=sample_user, provider="invalid", network="mainnet"
            )

    @pytest.mark.asyncio
    async def test_create_mpc_wallet_existing_belongs_to_other(self, service, mock_db, sample_user):
        """Test MPC wallet creation when wallet exists but belongs to another user."""
        wallet_data = {
            "wallet_id": "privy_wallet_123",
            "address": "0x1234567890123456789012345678901234567890",
        }

        existing_wallet = MagicMock()
        existing_wallet.user_id = 999  # Different user

        with patch("app.services.wallet_auth_service.WalletProviderFactory") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.create_wallet = AsyncMock(return_value=wallet_data)
            mock_provider.initialize = AsyncMock()
            mock_factory.get_provider = AsyncMock(return_value=mock_provider)

            with patch("app.services.wallet_auth_service.WalletRepository") as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_class.return_value = mock_repo_instance

                mock_result = MagicMock()
                mock_result.scalar_one_or_none = MagicMock(return_value=existing_wallet)
                mock_db.execute = AsyncMock(return_value=mock_result)

                with pytest.raises(
                    ValueError, match="Wallet already exists and belongs to another user"
                ):
                    await service.create_mpc_wallet(
                        db=mock_db, user=sample_user, provider="privy", network="mainnet"
                    )

    @pytest.mark.asyncio
    async def test_link_wallet_to_user_new(self, service, mock_db, sample_user):
        """Test linking new wallet to user."""
        wallet_address = "0x1234567890123456789012345678901234567890"

        # Mock database queries
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=None)  # No existing connection
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=None)  # No primary wallet
        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", 1))

        result = await service.link_wallet_to_user(
            db=mock_db,
            user=sample_user,
            wallet_address=wallet_address,
            wallet_type=WalletType.MPC,
            provider="privy",
            provider_wallet_id="wallet_123",
        )

        assert result is not None
        assert result.wallet_address == wallet_address
        assert result.wallet_type == WalletType.MPC
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_wallet_to_user_existing(self, service, mock_db, sample_user):
        """Test linking wallet when connection already exists."""
        wallet_address = "0x1234567890123456789012345678901234567890"

        existing_conn = WalletConnection(
            id=1,
            user_id=sample_user.id,
            wallet_address=wallet_address,
            wallet_type=WalletType.EXTERNAL,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_conn)
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", 1))

        result = await service.link_wallet_to_user(
            db=mock_db,
            user=sample_user,
            wallet_address=wallet_address,
            wallet_type=WalletType.MPC,
            provider="privy",
        )

        assert result.wallet_type == WalletType.MPC
        assert result.verified is True

    @pytest.mark.asyncio
    async def test_get_user_wallet_connections(self, service, mock_db, sample_user):
        """Test getting user wallet connections."""
        conn1 = WalletConnection(id=1, user_id=sample_user.id, wallet_address="0x111")
        conn2 = WalletConnection(id=2, user_id=sample_user.id, wallet_address="0x222")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [conn1, conn2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_wallet_connections(db=mock_db, user=sample_user)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
