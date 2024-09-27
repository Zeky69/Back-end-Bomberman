# routers/game.py
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.game_service import game_loop, place_bomb, broadcast_game_state
from app.models.models import Game, Bomb, Explosion
from typing import Dict, List
import json
from app.models.Player import Player

router = APIRouter()
games: Dict[str, Game] = {}
active_connections: Dict[str, List[WebSocket]] = {}



@router.websocket("/ws/game/{room_id}")
async def game_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in games:
        await websocket.close(code=1001)  # Partie inexistante
        return

    game = games[room_id]

    if room_id not in active_connections:
        active_connections[room_id] = []

    active_connections[room_id].append(websocket)
    player_id = str(websocket)  # Remplacer par un identifiant réel après authentification
    player = Player(id=player_id, username="player", x=1.0, y=1.0)
    game.add_player(player)

    # Démarrer la boucle de jeu si elle n'est pas déjà en cours
    if not any(task for task in asyncio.all_tasks() if task.get_coro() == game_loop(game)):
        asyncio.create_task(game_loop(game))

    try:
        while game.is_active:
            data = await websocket.receive_text()
            action_data = json.loads(data)

            action = action_data.get("action")
            if action == "move_start":
                direction = action_data.get("direction")
                if direction in ["up", "down", "left", "right"]:
                    player.moving_direction = direction
            elif action == "move_stop":
                player.moving_direction = None
            elif action == "place_bomb":
                x = action_data.get("x")
                y = action_data.get("y")
                place_bomb(game, player.id, x, y)

            # Les mises à jour sont déjà gérées par la boucle de jeu
    except WebSocketDisconnect:
        active_connections[room_id].remove(websocket)
        game.remove_player(player_id)
        if not active_connections[room_id]:
            game.is_active = False

async def broadcast_game_state(game: Game):
    state = game.state.dict()
    room_id = game.room_id
    if room_id in active_connections:
        connections = active_connections[room_id]
        for connection in connections:
            await connection.send_json(state)
