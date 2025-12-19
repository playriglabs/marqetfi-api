"""Test Ostium settlement provider."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from web3 import Web3

from app.config.providers.ostium import OstiumConfig
from app.services.providers.exceptions import SettlementProviderError
from app.services.providers.ostium.base import OstiumService
from app.services.providers.ostium.settlement import OstiumSettlementProvider


class TestOstiumSettlementProvider:
    """Test OstiumSettlementProvider class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return OstiumConfig(
            private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            rpc_url="https://rpc.example.com",
            network="testnet",
        )

    @pytest.fixture
    def provider(self, config):
        """Create test provider."""
        return OstiumSettlementProvider(config)

    @pytest.fixture
    def mock_ostium_service(self, provider):
        """Create mock OstiumService."""
        mock_service = MagicMock(spec=OstiumService)
        mock_service.initialize = AsyncMock()
        mock_service.health_check = AsyncMock(return_value=True)
        mock_service.handle_service_error = MagicMock(side_effect=lambda e, op: e)
        provider.ostium_service = mock_service
        return mock_service

    @pytest.fixture
    def mock_web3(self):
        """Create mock Web3 instance."""
        mock_web3 = MagicMock(spec=Web3)
        mock_web3.eth = MagicMock()
        return mock_web3

    @pytest.mark.asyncio
    async def test_get_transaction_status_confirmed(self, provider, mock_ostium_service, mock_web3):
        """Test get_transaction_status returns confirmed status."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        # Mock transaction
        mock_tx = {
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x2222222222222222222222222222222222222222",
            "value": 1000000,
        }

        # Mock receipt (status=1 means confirmed)
        mock_receipt = {
            "status": 1,
            "blockNumber": 12345,
            "blockHash": MagicMock(hex=lambda: "0xblockhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,  # get_transaction
                mock_receipt,  # get_transaction_receipt
                12350,  # block_number
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["transaction_hash"] == tx_hash
        assert result["status"] == "confirmed"
        assert result["block_number"] == 12345
        assert result["block_hash"] == "0xblockhash"
        assert result["gas_used"] == 21000
        assert result["confirmations"] == 5
        assert result["from"] == "0x1111111111111111111111111111111111111111"
        assert result["to"] == "0x2222222222222222222222222222222222222222"
        assert result["value"] == "1000000"

    @pytest.mark.asyncio
    async def test_get_transaction_status_failed(self, provider, mock_ostium_service, mock_web3):
        """Test get_transaction_status returns failed status."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 0,  # Failed transaction
            "blockNumber": 12345,
            "blockHash": MagicMock(hex=lambda: "0xblockhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,
                mock_receipt,
                12350,
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["status"] == "failed"
        assert result["block_number"] == 12345

    @pytest.mark.asyncio
    async def test_get_transaction_status_pending(self, provider, mock_ostium_service, mock_web3):
        """Test get_transaction_status returns pending status."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}

        mock_ostium_service.get_web3.return_value = mock_web3
        # First call succeeds (transaction exists), second fails (no receipt = pending)
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,  # get_transaction succeeds
                Exception("Transaction receipt not found"),  # get_transaction_receipt fails
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["transaction_hash"] == tx_hash
        assert result["status"] == "pending"
        assert result["from"] == "0x1111"
        assert result["to"] == "0x2222"

    @pytest.mark.asyncio
    async def test_get_transaction_status_not_found(self, provider, mock_ostium_service, mock_web3):
        """Test get_transaction_status returns not_found status."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=Exception("Transaction not found")
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["transaction_hash"] == tx_hash
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_transaction_status_hash_normalization(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status normalizes transaction hash (adds 0x prefix)."""
        tx_hash = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"  # No 0x

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 12345,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[mock_tx, mock_receipt, 12350]
        )

        result = await provider.get_transaction_status(tx_hash)

        # Verify that _execute_with_retry was called with 0x-prefixed hash
        calls = mock_ostium_service._execute_with_retry.call_args_list
        # First call should be get_transaction with 0x-prefixed hash
        assert "0x" in str(calls[0])
        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_get_transaction_status_with_0x_prefix(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status works with 0x-prefixed hash."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 12345,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[mock_tx, mock_receipt, 12350]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_get_transaction_status_network_error(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status handles network errors."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=ConnectionError("Network error")
        )
        mock_ostium_service.handle_service_error = MagicMock(
            side_effect=lambda e, op: SettlementProviderError(
                str(e), service_name="ostium-settlement"
            )
        )

        with pytest.raises(SettlementProviderError):
            await provider.get_transaction_status(tx_hash)

    @pytest.mark.asyncio
    async def test_get_transaction_status_initializes_service(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status initializes service if needed."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 12345,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[mock_tx, mock_receipt, 12350]
        )

        await provider.get_transaction_status(tx_hash)

        mock_ostium_service.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transaction_status_confirmations_calculation(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status calculates confirmations correctly."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 100,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,
                mock_receipt,
                150,  # Current block number
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["confirmations"] == 50  # 150 - 100

    @pytest.mark.asyncio
    async def test_get_transaction_status_zero_confirmations(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status handles zero confirmations."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 100,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,
                mock_receipt,
                100,  # Same block number
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["confirmations"] == 0  # max(0, 100 - 100)

    @pytest.mark.asyncio
    async def test_get_transaction_status_negative_confirmations(
        self, provider, mock_ostium_service, mock_web3
    ):
        """Test get_transaction_status handles negative confirmations (should be 0)."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        mock_tx = {"from": "0x1111", "to": "0x2222", "value": 0}
        mock_receipt = {
            "status": 1,
            "blockNumber": 100,
            "blockHash": MagicMock(hex=lambda: "0xhash"),
            "gasUsed": 21000,
        }

        mock_ostium_service.get_web3.return_value = mock_web3
        mock_ostium_service._execute_with_retry = AsyncMock(
            side_effect=[
                mock_tx,
                mock_receipt,
                50,  # Current block is less than transaction block (shouldn't happen, but test edge case)
            ]
        )

        result = await provider.get_transaction_status(tx_hash)

        assert result["confirmations"] == 0  # max(0, 50 - 100)
