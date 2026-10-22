import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from settings import WS_QUEUE_SIZE

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: dict[WebSocket, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> asyncio.Queue:
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=WS_QUEUE_SIZE)
        async with self._lock:
            self._clients[websocket] = queue
        return queue

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(websocket, None)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass

    async def broadcast(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._clients.values())
        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                continue

    async def pump(self, websocket: WebSocket, queue: asyncio.Queue) -> None:
        try:
            while True:
                payload = await queue.get()
                await websocket.send_json(payload)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception:
            logger.debug("WebSocket send ended", exc_info=True)
        finally:
            await self.disconnect(websocket)


manager = ConnectionManager()
