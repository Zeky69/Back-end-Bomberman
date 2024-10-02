# app/services/game_service.py

from typing import Dict, List
from app.repositories.redis_repository import RedisRepository
from app.models.game_models import GameState, Bomb
import asyncio

class GameService:
    def __init__(self, redis_repo: RedisRepository):
        self.redis = redis_repo

    async def start_game(self, room_id: str, players: List[str]):
        await self.redis.set_game_started(room_id)
        initial_state = {
            "players": {player: {"position": [0, 0], "bombs": 0} for player in players},
            "map": self.generate_initial_map(),
            "bombs": [],
            "explosions": []
        }
        await self.redis.set_game_state(room_id, initial_state)
        return initial_state

    def generate_initial_map(self):
        # Implémentez la logique pour générer une carte de jeu initiale
        return {
            "width": 15,
            "height": 15,
            "walls": self.generate_walls(),
            "bombs": [],
            "explosions": []
        }

    def generate_walls(self):
        # Exemple simplifié : créer des murs aux positions paires
        walls = []
        for x in range(15):
            for y in range(15):
                if x % 2 == 0 and y % 2 == 0:
                    walls.append([x, y])
        return walls

    async def handle_game_action(self, room_id: str, username: str, action: dict):
        if not await self.redis.is_game_started(room_id):
            raise ValueError("Le jeu n'a pas encore commencé")

        game_state = await self.redis.get_game_state(room_id)
        updated_state = self.process_action(game_state, username, action)
        await self.redis.set_game_state(room_id, updated_state)
        return updated_state

    def process_action(self, game_state: dict, username: str, action: dict) -> dict:
        player = game_state["players"].get(username)
        if not player:
            return game_state

        if action["type"] == "move":
            direction = action.get("direction")
            if direction:
                if direction == "up":
                    player["position"][1] -= 1
                elif direction == "down":
                    player["position"][1] += 1
                elif direction == "left":
                    player["position"][0] -= 1
                elif direction == "right":
                    player["position"][0] += 1

        elif action["type"] == "place_bomb":
            if player["bombs"] < 1:  # Limiter le nombre de bombes par joueur
                bomb = Bomb(position=player["position"].copy(), owner=username, timer=3)
                game_state["bombs"].append(bomb.dict())
                player["bombs"] += 1

        # Ajoutez d'autres types d'actions selon les besoins

        return game_state

    async def game_loop(self, room_id: str):
        while await self.redis.is_game_started(room_id):
            game_state = await self.redis.get_game_state(room_id)
            # Logique pour gérer les bombes et les explosions
            updated_bombs = []
            for bomb in game_state["bombs"]:
                bomb["timer"] -= 1
                if bomb["timer"] <= 0:
                    # Gérer l'explosion
                    # Mettre à jour les positions des joueurs, les murs, etc.
                    self.handle_explosion(game_state, bomb)
                else:
                    updated_bombs.append(bomb)
            game_state["bombs"] = updated_bombs
            await self.redis.set_game_state(room_id, game_state)
            await asyncio.sleep(1)  # Intervalle de mise à jour (1 seconde)

    def handle_explosion(self, game_state: dict, bomb: dict):
        # Implémentez la logique des explosions
        # Par exemple, éliminer les joueurs proches, détruire les murs, etc.
        explosion_position = bomb["position"]
        # Exemple simplifié : ajouter l'explosion à l'état du jeu
        game_state["explosions"].append({"position": explosion_position})
        # Réinitialiser le nombre de bombes pour le joueur
        owner = bomb["owner"]
        if owner in game_state["players"]:
            game_state["players"][owner]["bombs"] -= 1
