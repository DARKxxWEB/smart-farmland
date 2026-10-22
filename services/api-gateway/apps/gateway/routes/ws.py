import asyncio
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from auth.v1 import auth_pb2
from grpc_clients import clients
from utils.ws_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["realtime"])


async def _authenticate(websocket: WebSocket, token: str) -> bool:
    header = websocket.headers.get("authorization", "")
    scheme, _, bearer = header.partition(" ")
    access_token = token or (bearer if scheme.lower() == "bearer" else "")
    if not access_token:
        await websocket.close(code=4401)
        return False
    try:
        result = await clients.auth_stub.VerifyToken(
            auth_pb2.VerifyTokenRequest(access_token=access_token)
        )
    except Exception:
        await websocket.close(code=1011)
        return False
    if not result.valid:
        await websocket.close(code=4401)
        return False
    return True


@router.websocket("/api/v1/ws/telemetry")
async def telemetry_stream(
    websocket: WebSocket,
    access_token: str = Query(default=""),
):
    if not await _authenticate(websocket, access_token):
        return

    queue = await manager.connect(websocket)
    sender = asyncio.create_task(manager.pump(websocket, queue))
    try:
        while True:
            message = await websocket.receive_text()
            if message in {"ping", "heartbeat"}:
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info("Telemetry websocket closed")
    except Exception:
        logger.debug("Telemetry websocket ended", exc_info=True)
    finally:
        sender.cancel()
        await manager.disconnect(websocket)
