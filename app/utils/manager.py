from typing import Dict

from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        # room_id -> Dict[username, WebSocket]
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, username: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][username] = websocket

    def disconnect(self, room_id: str, username: str):
        if room_id in self.active_connections:
            if username in self.active_connections[room_id]:
                del self.active_connections[room_id][username]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_json(message)
