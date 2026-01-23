"""Test WebhookService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.webhook_service import WebhookService


class TestWebhookService:
    """Test WebhookService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create WebhookService instance."""
        return WebhookService(db=mock_db)

    @pytest.fixture
    def mock_webhook(self):
        """Create mock webhook configuration."""
        webhook = MagicMock()
        webhook.id = 1
        webhook.url = "https://example.com/webhook"
        webhook.secret = "test_secret_key_123"
        webhook.event_types = ["order.created", "order.updated"]
        webhook.is_active = True
        return webhook

    @pytest.fixture
    def mock_delivery(self):
        """Create mock webhook delivery."""
        delivery = MagicMock()
        delivery.id = 1
        delivery.webhook_id = 1
        delivery.delivery_id = "test-delivery-uuid"
        delivery.success = False
        delivery.retry_count = 0
        return delivery

    @pytest.mark.asyncio
    async def test_send_webhook_no_active_webhooks(self, service, mock_db):
        """Test sending webhook when no active webhooks exist."""
        service.webhook_repo.get_active_by_event_type = AsyncMock(return_value=[])

        await service.send_webhook(
            user_id=1,
            event_type="order.created",
            event_data={"order_id": 123},
        )

        service.webhook_repo.get_active_by_event_type.assert_called_once_with(
            mock_db, 1, "order.created"
        )

    @pytest.mark.asyncio
    async def test_send_webhook_creates_delivery(self, service, mock_db, mock_webhook):
        """Test webhook creates delivery record."""
        service.webhook_repo.get_active_by_event_type = AsyncMock(return_value=[mock_webhook])
        service.delivery_repo.create = AsyncMock(return_value=MagicMock(id=1))

        with patch("asyncio.create_task"):
            await service.send_webhook(
                user_id=1,
                event_type="order.created",
                event_data={"order_id": 123},
            )

        service.delivery_repo.create.assert_called_once()
        call_args = service.delivery_repo.create.call_args[0]
        assert call_args[0] == mock_db
        delivery_data = call_args[1]
        assert delivery_data["webhook_id"] == 1
        assert delivery_data["event_type"] == "order.created"
        assert delivery_data["success"] is False

    @pytest.mark.asyncio
    async def test_generate_hmac(self, service):
        """Test HMAC signature generation."""
        payload = {"event_type": "order.created", "data": {"order_id": 123}}
        secret = "test_secret"

        signature = service._generate_hmac(secret, payload)

        assert isinstance(signature, str)
        assert len(signature) == 64

    @pytest.mark.asyncio
    async def test_generate_hmac_deterministic(self, service):
        """Test HMAC generation is deterministic."""
        payload = {"event_type": "order.created", "data": {"order_id": 123}}
        secret = "test_secret"

        sig1 = service._generate_hmac(secret, payload)
        sig2 = service._generate_hmac(secret, payload)

        assert sig1 == sig2

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, service):
        """Test webhook signature verification with valid signature."""
        payload = {"event_type": "order.created", "data": {"order_id": 123}}
        secret = "test_secret"

        signature = service._generate_hmac(secret, payload)
        result = await service.verify_webhook_signature(secret, payload, signature)

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self, service):
        """Test webhook signature verification with invalid signature."""
        payload = {"event_type": "order.created", "data": {"order_id": 123}}
        secret = "test_secret"

        result = await service.verify_webhook_signature(secret, payload, "invalid_signature")

        assert result is False

    @pytest.mark.asyncio
    async def test_deliver_with_retry_success(self, service, mock_db, mock_delivery):
        """Test successful webhook delivery on first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        service.http_client.post = AsyncMock(return_value=mock_response)
        service.delivery_repo.get = AsyncMock(return_value=mock_delivery)
        service.webhook_repo.update_last_delivery = AsyncMock()

        await service._deliver_with_retry(
            delivery_id=1,
            webhook_id=1,
            url="https://example.com/webhook",
            payload={"event_type": "test"},
            signature="test_sig",
            delivery_uuid="test-uuid",
        )

        assert mock_delivery.success is True
        assert mock_delivery.status_code == 200
        assert mock_delivery.retry_count == 1
        mock_db.commit.assert_called()
        service.webhook_repo.update_last_delivery.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_deliver_with_retry_failure_with_retries(self, service, mock_db, mock_delivery):
        """Test webhook delivery retries on failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        service.http_client.post = AsyncMock(return_value=mock_response)
        service.delivery_repo.get = AsyncMock(return_value=mock_delivery)
        service.delivery_repo.count_failures_by_delivery_id = AsyncMock(return_value=4)
        service.webhook_repo.disable_webhook = AsyncMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await service._deliver_with_retry(
                delivery_id=1,
                webhook_id=1,
                url="https://example.com/webhook",
                payload={"event_type": "test"},
                signature="test_sig",
                delivery_uuid="test-uuid",
            )

        assert service.http_client.post.call_count == service.MAX_RETRY_ATTEMPTS
        service.webhook_repo.disable_webhook.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_deliver_with_retry_timeout(self, service, mock_db, mock_delivery):
        """Test webhook delivery handles timeout."""
        service.http_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        service.delivery_repo.get = AsyncMock(return_value=mock_delivery)
        service.delivery_repo.count_failures_by_delivery_id = AsyncMock(return_value=4)
        service.webhook_repo.disable_webhook = AsyncMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await service._deliver_with_retry(
                delivery_id=1,
                webhook_id=1,
                url="https://example.com/webhook",
                payload={"event_type": "test"},
                signature="test_sig",
                delivery_uuid="test-uuid",
            )

        assert mock_delivery.error_message == "Timeout"
        assert mock_delivery.success is False
        service.webhook_repo.disable_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_with_retry_exception(self, service, mock_db, mock_delivery):
        """Test webhook delivery handles exceptions."""
        service.http_client.post = AsyncMock(side_effect=Exception("Network error"))
        service.delivery_repo.get = AsyncMock(return_value=mock_delivery)
        service.delivery_repo.count_failures_by_delivery_id = AsyncMock(return_value=4)
        service.webhook_repo.disable_webhook = AsyncMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await service._deliver_with_retry(
                delivery_id=1,
                webhook_id=1,
                url="https://example.com/webhook",
                payload={"event_type": "test"},
                signature="test_sig",
                delivery_uuid="test-uuid",
            )

        assert "Network error" in mock_delivery.error_message
        service.webhook_repo.disable_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_success_on_retry(self, service, mock_db, mock_delivery):
        """Test webhook succeeds after retries."""
        mock_failure = MagicMock()
        mock_failure.status_code = 500
        mock_failure.text = "Error"

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.text = "OK"

        service.http_client.post = AsyncMock(side_effect=[mock_failure, mock_success])
        service.delivery_repo.get = AsyncMock(return_value=mock_delivery)
        service.webhook_repo.update_last_delivery = AsyncMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await service._deliver_with_retry(
                delivery_id=1,
                webhook_id=1,
                url="https://example.com/webhook",
                payload={"event_type": "test"},
                signature="test_sig",
                delivery_uuid="test-uuid",
            )

        assert service.http_client.post.call_count == 2
        assert mock_delivery.success is True
        service.webhook_repo.update_last_delivery.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test closing HTTP client."""
        service.http_client.aclose = AsyncMock()

        await service.close()

        service.http_client.aclose.assert_called_once()
