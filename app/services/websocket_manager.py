"""WebSocket connection manager service."""

import asyncio
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import logger


class WebSocketManager:
    """Manages WebSocket connections with heartbeat and partial authentication.

    Public channels (trades, prices): Anonymous access allowed
    Private channels (orders, positions): JWT authentication required
    """

    # Channel access control
    PUBLIC_CHANNELS = {"trades", "prices"}
    PRIVATE_CHANNELS = {"orders", "positions"}

    # Configuration
    HEARTBEAT_INTERVAL = 30  # seconds
    HEARTBEAT_TIMEOUT = 60  # seconds
    MAX_SUBSCRIPTIONS_PER_CONNECTION = 10

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        # conn_id -> WebSocket instance
        self.connections: dict[str, WebSocket] = {}
        # conn_id -> set of subscribed channels
        self.subscriptions: dict[str, set[str]] = {}
        # conn_id -> heartbeat task
        self.heartbeat_tasks: dict[str, asyncio.Task[None]] = {}
        # conn_id -> user_id (None for anonymous)
        self.connection_users: dict[str, str | None] = {}
        # channel -> set of conn_ids
        self.channel_subscribers: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str | None = None) -> str:
        """Accept WebSocket connection and register it.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user ID (None for anonymous)

        Returns:
            Connection ID for this connection
        """
        await websocket.accept()

        conn_id = user_id if user_id else f"anon_{id(websocket)}"

        self.connections[conn_id] = websocket
        self.subscriptions[conn_id] = set()
        self.connection_users[conn_id] = user_id

        self.heartbeat_tasks[conn_id] = asyncio.create_task(
            self._heartbeat_loop(conn_id, websocket)
        )

        logger.info(f"WebSocket connected: {conn_id} (authenticated: {user_id is not None})")
        return conn_id

    async def disconnect(self, conn_id: str) -> None:
        """Disconnect and cleanup WebSocket connection.

        Args:
            conn_id: Connection ID to disconnect
        """
        if conn_id in self.heartbeat_tasks:
            self.heartbeat_tasks[conn_id].cancel()
            del self.heartbeat_tasks[conn_id]

        if conn_id in self.subscriptions:
            for channel in self.subscriptions[conn_id].copy():
                await self.unsubscribe(conn_id, channel)
            del self.subscriptions[conn_id]

        if conn_id in self.connections:
            del self.connections[conn_id]

        if conn_id in self.connection_users:
            del self.connection_users[conn_id]

        logger.info(f"WebSocket disconnected: {conn_id}")

    async def subscribe(self, conn_id: str, channel: str) -> dict[str, Any]:
        """Subscribe connection to a channel.

        Args:
            conn_id: Connection ID
            channel: Channel name to subscribe to

        Returns:
            Response dict with success status or error

        Raises:
            ValueError: If connection not found or rate limit exceeded
        """
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")

        if len(self.subscriptions[conn_id]) >= self.MAX_SUBSCRIPTIONS_PER_CONNECTION:
            return {
                "type": "error",
                "channel": channel,
                "error": f"Maximum {self.MAX_SUBSCRIPTIONS_PER_CONNECTION} subscriptions exceeded",
            }

        user_id = self.connection_users[conn_id]
        if channel in self.PRIVATE_CHANNELS and user_id is None:
            return {
                "type": "error",
                "channel": channel,
                "error": "Authentication required for private channels",
            }

        all_channels = self.PUBLIC_CHANNELS | self.PRIVATE_CHANNELS
        if channel not in all_channels:
            return {
                "type": "error",
                "channel": channel,
                "error": f"Unknown channel: {channel}",
            }

        if channel in self.subscriptions[conn_id]:
            return {
                "type": "subscribed",
                "channel": channel,
                "message": "Already subscribed",
            }

        self.subscriptions[conn_id].add(channel)

        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(conn_id)

        logger.info(f"WebSocket {conn_id} subscribed to {channel}")
        return {
            "type": "subscribed",
            "channel": channel,
            "message": "Successfully subscribed",
        }

    async def unsubscribe(self, conn_id: str, channel: str) -> dict[str, Any]:
        """Unsubscribe connection from a channel.

        Args:
            conn_id: Connection ID
            channel: Channel name to unsubscribe from

        Returns:
            Response dict with success status
        """
        if conn_id not in self.subscriptions:
            return {
                "type": "error",
                "channel": channel,
                "error": f"Connection {conn_id} not found",
            }

        if channel in self.subscriptions[conn_id]:
            self.subscriptions[conn_id].remove(channel)

        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(conn_id)
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]

        logger.info(f"WebSocket {conn_id} unsubscribed from {channel}")
        return {
            "type": "unsubscribed",
            "channel": channel,
            "message": "Successfully unsubscribed",
        }

    async def broadcast_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast message to all subscribers of a channel.

        Args:
            channel: Channel name
            message: Message dict to broadcast
        """
        if channel not in self.channel_subscribers:
            return

        subscribers = self.channel_subscribers[channel].copy()

        for conn_id in subscribers:
            if conn_id in self.connections:
                try:
                    await self.connections[conn_id].send_json(message)
                except WebSocketDisconnect:
                    await self.disconnect(conn_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {conn_id}: {e}")
                    await self.disconnect(conn_id)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send message to specific user's connection.

        Args:
            user_id: User ID
            message: Message dict to send
        """
        if user_id in self.connections:
            try:
                await self.connections[user_id].send_json(message)
            except WebSocketDisconnect:
                await self.disconnect(user_id)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                await self.disconnect(user_id)

    async def _heartbeat_loop(self, conn_id: str, websocket: WebSocket) -> None:
        """Send periodic pings to keep connection alive.

        Args:
            conn_id: Connection ID
            websocket: WebSocket instance
        """
        try:
            while True:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                await websocket.send_json({"type": "ping"})
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.error(f"Heartbeat error for {conn_id}: {e}")
        finally:
            await self.disconnect(conn_id)


websocket_manager = WebSocketManager()
