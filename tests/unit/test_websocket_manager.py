"""Test WebSocketManager."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket

from app.services.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Test WebSocketManager class."""

    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance."""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = MagicMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    def teardown_method(self):
        """Cancel all pending tasks after each test."""
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        for task in tasks:
            task.cancel()

    @pytest.mark.asyncio
    async def test_connect_authenticated(self, manager, mock_websocket):
        """Test connecting with authentication."""
        user_id = "user_123"

        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, user_id)

            assert conn_id == user_id
            assert conn_id in manager.connections
            assert conn_id in manager.subscriptions
            assert conn_id in manager.connection_users
            assert manager.connection_users[conn_id] == user_id
            mock_websocket.accept.assert_called_once()

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_connect_anonymous(self, manager, mock_websocket):
        """Test connecting without authentication."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, user_id=None)

            assert conn_id.startswith("anon_")
            assert conn_id in manager.connections
            assert manager.connection_users[conn_id] is None
            mock_websocket.accept.assert_called_once()

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, "user_123")

            await manager.disconnect(conn_id)

            assert conn_id not in manager.connections
            assert conn_id not in manager.subscriptions
            assert conn_id not in manager.connection_users

    @pytest.mark.asyncio
    async def test_subscribe_public_channel_anonymous(self, manager, mock_websocket):
        """Test anonymous user subscribing to public channel."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, user_id=None)

            result = await manager.subscribe(conn_id, "trades")

            assert result["type"] == "subscribed"
            assert result["channel"] == "trades"
            assert "trades" in manager.subscriptions[conn_id]
            assert conn_id in manager.channel_subscribers["trades"]

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_subscribe_private_channel_requires_auth(self, manager, mock_websocket):
        """Test anonymous user cannot subscribe to private channel."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, user_id=None)

            result = await manager.subscribe(conn_id, "orders")

            assert result["type"] == "error"
            assert "Authentication required" in result["error"]
            assert "orders" not in manager.subscriptions[conn_id]

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_subscribe_private_channel_authenticated(self, manager, mock_websocket):
        """Test authenticated user can subscribe to private channel."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, "user_123")

            result = await manager.subscribe(conn_id, "orders")

            assert result["type"] == "subscribed"
            assert result["channel"] == "orders"
            assert "orders" in manager.subscriptions[conn_id]

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_subscribe_rate_limit(self, manager, mock_websocket):
        """Test rate limiting max subscriptions per connection."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, "user_123")

            manager.subscriptions[conn_id] = {
                f"channel_{i}" for i in range(manager.MAX_SUBSCRIPTIONS_PER_CONNECTION)
            }

            result = await manager.subscribe(conn_id, "orders")

            assert result["type"] == "error"
            assert "Maximum" in result["error"]

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_subscribe_unknown_channel(self, manager, mock_websocket):
        """Test subscribing to unknown channel."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, "user_123")

            result = await manager.subscribe(conn_id, "invalid_channel")

            assert result["type"] == "error"
            assert "Unknown channel" in result["error"]

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_subscribe_invalid_connection(self, manager):
        """Test subscribing with invalid connection ID."""
        with pytest.raises(ValueError, match="not found"):
            await manager.subscribe("invalid_conn", "trades")

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager, mock_websocket):
        """Test unsubscribing from channel."""
        with patch_heartbeat():
            conn_id = await manager.connect(mock_websocket, "user_123")
            await manager.subscribe(conn_id, "trades")

            result = await manager.unsubscribe(conn_id, "trades")

            assert result["type"] == "unsubscribed"
            assert "trades" not in manager.subscriptions[conn_id]
            assert "trades" not in manager.channel_subscribers

            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager):
        """Test broadcasting message to channel subscribers."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        with patch_heartbeat():
            conn_id1 = await manager.connect(ws1, "user_1")
            conn_id2 = await manager.connect(ws2, "user_2")

            await manager.subscribe(conn_id1, "trades")
            await manager.subscribe(conn_id2, "trades")

            message = {"type": "trade", "data": {"price": 100}}
            await manager.broadcast_to_channel("trades", message)

            ws1.send_json.assert_called_once_with(message)
            ws2.send_json.assert_called_once_with(message)

            await manager.disconnect(conn_id1)
            await manager.disconnect(conn_id2)

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        """Test sending message to specific user."""
        with patch_heartbeat():
            user_id = "user_123"
            conn_id = await manager.connect(mock_websocket, user_id)

            message = {"type": "notification", "data": "test"}
            await manager.send_to_user(user_id, message)

            mock_websocket.send_json.assert_called_once_with(message)

            await manager.disconnect(conn_id)


def patch_heartbeat():
    """Context manager to disable heartbeat during tests."""
    from unittest.mock import patch

    async def noop_heartbeat(*args, **kwargs):
        pass

    return patch("app.services.websocket_manager.WebSocketManager._heartbeat_loop", noop_heartbeat)
