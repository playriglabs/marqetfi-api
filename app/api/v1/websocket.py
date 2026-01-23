"""WebSocket endpoint for real-time updates."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.logging import logger
from app.core.security import decode_token
from app.services.websocket_manager import websocket_manager

router = APIRouter()


async def get_user_from_token(token: str | None) -> str | None:
    """Extract user ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID or None if invalid/missing
    """
    if not token:
        return None

    try:
        payload = await decode_token(token)
        if payload is None:
            return None

        sub = payload.get("sub")
        if isinstance(sub, str):
            return sub
        elif isinstance(sub, int):
            return str(sub)

        user_id = payload.get("user_id")
        if user_id:
            return str(user_id)

        return None
    except (JWTError, Exception) as e:
        logger.debug(f"Failed to decode WebSocket token: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Public channels (no auth required):
    - trades: Trade execution updates
    - prices: Real-time price updates

    Private channels (JWT required):
    - orders: User's order updates
    - positions: User's position updates

    Message format:
    - Subscribe: {"type": "subscribe", "channel": "trades"}
    - Unsubscribe: {"type": "unsubscribe", "channel": "trades"}
    - Ping: {"type": "ping"} (auto-sent every 30s)
    - Pong: {"type": "pong"} (client response to ping)

    Response format:
    - Success: {"type": "subscribed", "channel": "trades"}
    - Error: {"type": "error", "channel": "orders", "error": "message"}
    """
    token = None
    for header_name, header_value in websocket.headers.items():
        if header_name.lower() == "authorization":
            if header_value.startswith("Bearer "):
                token = header_value[7:]
            break

    user_id = await get_user_from_token(token)

    conn_id = await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    channel = message.get("channel")
                    if not channel:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Channel is required",
                            }
                        )
                        continue

                    result = await websocket_manager.subscribe(conn_id, channel)
                    await websocket.send_json(result)

                elif message_type == "unsubscribe":
                    channel = message.get("channel")
                    if not channel:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Channel is required",
                            }
                        )
                        continue

                    result = await websocket_manager.unsubscribe(conn_id, channel)
                    await websocket.send_json(result)

                elif message_type == "pong":
                    pass

                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": f"Unknown message type: {message_type}",
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": "Invalid JSON",
                    }
                )
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": "Internal error",
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conn_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {conn_id}: {e}")
    finally:
        await websocket_manager.disconnect(conn_id)
