"""Test WalletSigner class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from eth_account import Account

from app.core.wallet_signer import WalletSigner
from app.services.wallet_providers.exceptions import WalletSigningError


class TestWalletSigner:
    """Test WalletSigner class."""

    @pytest.fixture
    def private_key(self):
        """Create test private key."""
        account = Account.create()
        return account.key.hex()

    @pytest.fixture
    def wallet_signer_private_key(self, private_key):
        """Create WalletSigner with private key."""
        return WalletSigner(private_key=private_key)

    @pytest.fixture
    def wallet_signer_provider(self):
        """Create WalletSigner with provider."""
        return WalletSigner(wallet_provider="privy", wallet_id="wallet_123")

    @pytest.mark.asyncio
    async def test_sign_transaction_private_key(self, wallet_signer_private_key, private_key):
        """Test signing transaction with private key."""
        account = Account.from_key(private_key)
        transaction = {
            "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "value": 1000000000000000000,
            "gas": 21000,
            "gasPrice": 20000000000,
            "nonce": 0,
            "chainId": 1,
        }

        result = await wallet_signer_private_key.sign_transaction(transaction)

        assert "rawTransaction" in result
        assert "hash" in result

    @pytest.mark.asyncio
    async def test_sign_transaction_provider(self, wallet_signer_provider):
        """Test signing transaction with provider."""
        mock_provider = MagicMock()
        mock_provider.sign_transaction = AsyncMock(return_value="0x" + "a" * 200)  # Raw transaction

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            transaction = {
                "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "value": 1000000000000000000,
            }

            result = await wallet_signer_provider.sign_transaction(transaction)

            assert "rawTransaction" in result
            assert "hash" in result

    @pytest.mark.asyncio
    async def test_sign_transaction_provider_fallback(self, wallet_signer_provider, private_key):
        """Test signing transaction with provider fallback to private key."""
        wallet_signer_provider.private_key = private_key
        mock_provider = MagicMock()
        mock_provider.sign_transaction = AsyncMock(side_effect=Exception("Provider error"))

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            transaction = {
                "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "value": 1000000000000000000,
                "gas": 21000,
                "gasPrice": 20000000000,
                "nonce": 0,
                "chainId": 1,
            }

            result = await wallet_signer_provider.sign_transaction(transaction)

            assert "rawTransaction" in result

    @pytest.mark.asyncio
    async def test_sign_transaction_no_provider_no_key(self):
        """Test signing transaction with no provider and no key."""
        signer = WalletSigner()

        with pytest.raises(WalletSigningError, match="No wallet provider or private key"):
            await signer.sign_transaction({"to": "0x123"})

    @pytest.mark.asyncio
    async def test_sign_message_private_key(self, wallet_signer_private_key):
        """Test signing message with private key."""
        message = "Hello, World!"

        result = await wallet_signer_private_key.sign_message(message)

        assert result.startswith("0x")
        assert len(result) > 10

    @pytest.mark.asyncio
    async def test_sign_message_provider(self, wallet_signer_provider):
        """Test signing message with provider."""
        mock_provider = MagicMock()
        mock_provider.sign_message = AsyncMock(return_value="0x" + "b" * 130)

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            result = await wallet_signer_provider.sign_message("Hello")

            assert result.startswith("0x")

    @pytest.mark.asyncio
    async def test_sign_message_provider_fallback(self, wallet_signer_provider, private_key):
        """Test signing message with provider fallback to private key."""
        wallet_signer_provider.private_key = private_key
        mock_provider = MagicMock()
        mock_provider.sign_message = AsyncMock(side_effect=Exception("Provider error"))

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            result = await wallet_signer_provider.sign_message("Hello")

            assert result.startswith("0x")

    def test_get_address_private_key(self, wallet_signer_private_key, private_key):
        """Test getting address from private key."""
        account = Account.from_key(private_key)

        address = wallet_signer_private_key.get_address()

        assert address == account.address

    def test_get_address_no_key(self):
        """Test getting address when no key."""
        signer = WalletSigner()

        address = signer.get_address()

        assert address is None

    @pytest.mark.asyncio
    async def test_get_wallet_address_provider(self, wallet_signer_provider):
        """Test getting wallet address from provider."""
        mock_provider = MagicMock()
        mock_provider.get_wallet_address = AsyncMock(return_value="0x123")

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            address = await wallet_signer_provider.get_wallet_address()

            assert address == "0x123"

    @pytest.mark.asyncio
    async def test_get_wallet_address_provider_fallback(self, wallet_signer_provider, private_key):
        """Test getting wallet address with provider fallback."""
        wallet_signer_provider.private_key = private_key
        mock_provider = MagicMock()
        mock_provider.get_wallet_address = AsyncMock(side_effect=Exception("Provider error"))

        with patch(
            "app.core.wallet_signer.WalletProviderFactory.get_provider", return_value=mock_provider
        ):
            address = await wallet_signer_provider.get_wallet_address()

            assert address is not None
