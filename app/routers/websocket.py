# app/routers/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
from app.services.room_service import RoomService
from app.services.game_service import GameService
from app.repositories.redis_repository import RedisRepository
import asyncio
import json

from app.utils.manager import ConnectionManager

router = APIRouter()


manager = ConnectionManager()

@router.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str,
                             room_service: RoomService = Depends(lambda: RoomService(RedisRepository())),
                             game_service: GameService = Depends(lambda: GameService(RedisRepository(),manager))):
    await manager.connect(websocket, room_id, username)
    try:
        # Vérifier si la salle existe
        if not await room_service.redis.room_exists(room_id):
            await manager.send_personal_message({"error": "Salle inexistante"}, websocket)
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

        # Vérifier si le jeu a déjà démarré
        game_started = await game_service.redis.is_game_started(room_id)
        if game_started:
            # Envoyer l'état actuel du jeu au nouveau joueur
            game_state = await game_service.redis.get_game_state(room_id)
            await manager.send_personal_message({"event": "game_state", "state": game_state}, websocket)

        # Boucle principale pour recevoir les messages du client
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")

            if event == "start_game":
                # Vérifier si le jeu n'a pas déjà démarré
                if game_started:
                    await manager.send_personal_message({"error": "Le jeu a déjà démarré"}, websocket)
                    continue

                creator = await room_service.redis.redis.hget(f"room:{room_id}", "creator")
                # if username != creator.decode():
                #     await manager.send_personal_message({"error": "Seul le créateur peut lancer la partie"}, websocket)
                #     continue
                print(players)
                if len(players) < 2:
                    await manager.send_personal_message({"error": "Nombre de joueurs insuffisant pour démarrer la partie (2 minimum)"}, websocket)
                    continue

                # Lancer le jeu
                initial_state = await game_service.start_game(room_id, players)
                await manager.broadcast(room_id, {"event": "game_started"})
                await manager.broadcast(room_id, {"event": "game_state", "state": initial_state})

                # Démarrer la boucle de jeu
                asyncio.create_task(game_service.game_loop(room_id))

                game_started = True

            elif event == "game_action":
                action = message.get("action")
                try:
                    await game_service.handle_game_action(room_id, username, action)
                    # Diffuser l'action à tous les autres joueurs
                    await manager.broadcast(room_id, {
                        "event": "game_action",
                        "username": username,
                        "action": action
                    })
                except ValueError as e:
                    await manager.send_personal_message({"error": str(e)}, websocket)

            elif event == "request_state":
                # Permettre au client de demander l'état actuel du jeu
                game_state = await game_service.redis.get_game_state(room_id)
                await manager.send_personal_message({"event": "game_state", "state": game_state}, websocket)

            elif event == "chat_message":
                chat_message = message.get("message")
                await manager.broadcast(room_id, {
                    "event": "chat_message",
                    "username": username,
                    "message": chat_message
                })

    except WebSocketDisconnect:
        manager.disconnect(room_id, username)
        await room_service.redis.remove_player_from_room(room_id, username)
        players = await room_service.redis.get_room_players(room_id)
        await manager.broadcast(room_id, {
            "event": "player_left",
            "username": username,
            "players": list(players)
        })

        # Optionnel : Arrêter le jeu si plus assez de joueurs
        if len(players) < 2:
            await game_service.redis.set_game_started(room_id)
            await manager.broadcast(room_id, {"event": "game_stopped"})

