"""In-process WebSocket connection manager, one room per draft."""

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class DraftConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, draft_id: int, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._rooms[draft_id].add(ws)

    async def disconnect(self, draft_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._rooms[draft_id].discard(ws)

    async def broadcast(self, draft_id: int, event: dict) -> None:
        async with self._lock:
            targets = list(self._rooms.get(draft_id, ()))
        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception:
                await self.disconnect(draft_id, ws)


manager = DraftConnectionManager()
