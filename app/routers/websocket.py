# app/routers/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
from app.services.room_service import RoomService
from app.services.game_service import GameService
from app.repositories.redis_repository import RedisRepository
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # room_id -> List of WebSocket
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str,
                            room_service: RoomService = Depends(lambda: RoomService(RedisRepository())),
                            game_service: GameService = Depends(lambda: GameService(RedisRepository()))):
    await manager.connect(websocket, room_id)
    try:
        # Vérifier si la salle existe
        if not await room_service.redis.room_exists(room_id):
            await websocket.send_json({"error": "Salle inexistante"})
            await websocket.close()
            return

        # Ajouter le joueur à la salle
        await room_service.redis.add_player_to_room(room_id, username)
        players = await room_service.redis.get_room_players(room_id)
        await manager.broadcast(room_id, {
            "event": "player_joined",
            "username": username,
            "players": list(players)
        })

        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "start_game":
                creator = await room_service.redis.redis.hget(f"room:{room_id}", "creator")
                if username != creator:
                    await websocket.send_json({"error": "Seul le créateur peut lancer la partie"})
                    continue

                if len(players) < 2:
                    await websocket.send_json({"error": "Nombre de joueurs insuffisant pour démarrer la partie (2 minimum)"})
                    continue

                # Lancer le jeu
                initial_state = await game_service.start_game(room_id, players)
                await manager.broadcast(room_id, {"event": "game_started"})
                await manager.broadcast(room_id, {"event": "game_state", "state": initial_state})

                # Démarrer la boucle de jeu
                asyncio.create_task(game_service.game_loop(room_id))

            elif event == "game_action":
                action = data.get("action")
                try:
                    updated_state = await game_service.handle_game_action(room_id, username, action)
                    await manager.broadcast(room_id, {"event": "game_update", "state": updated_state})
                except ValueError as e:
                    await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await room_service.redis.remove_player_from_room(room_id, username)
        players = await room_service.redis.get_room_players(room_id)
        await manager.broadcast(room_id, {
            "event": "player_left",
            "username": username,
            "players": list(players)
        })
