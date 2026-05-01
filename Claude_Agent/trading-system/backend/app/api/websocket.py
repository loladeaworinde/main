from __future__ import annotations
import asyncio
import json
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_json(self, client_id: str, data: dict):
        ws = self.active.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception as e:
                logger.warning(f"WS send error for {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, data: dict):
        dead = []
        for client_id, ws in self.active.items():
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception:
                dead.append(client_id)
        for client_id in dead:
            self.disconnect(client_id)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    await manager.send_json(client_id, {
        "event": "connected",
        "client_id": client_id,
        "message": "Trading System WebSocket connected",
    })
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event", "")
            if event == "subscribe":
                symbol = msg.get("symbol", "")
                await manager.send_json(client_id, {"event": "subscribed", "symbol": symbol})
            elif event == "ping":
                await manager.send_json(client_id, {"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.warning(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)
