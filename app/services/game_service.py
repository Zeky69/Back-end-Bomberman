# app/services/game_service.py

from typing import Dict, List
from app.repositories.redis_repository import RedisRepository
from app.models.game_models import GameState, Bomb, PowerUp
import asyncio
import random
import time

from app.utils.manager import ConnectionManager


class GameService:
    def __init__(self, redis_repo: RedisRepository, manager: ConnectionManager):
        self.redis = redis_repo
        self.manager = manager

    async def start_game(self, room_id: str, players: List[str]):
        await self.redis.set_game_started(room_id)
        starting_positions = [
            [1.0, 1.0],
            [13.0, 1.0],
            [1.0, 13.0],
            [13.0, 13.0]
        ]
        initial_state = {
            "players": {},
            "map": self.generate_initial_map(),
            "bombs": [],
            "explosions": [],
            "powerups": [],
            "started_at": time.time()
        }
        for idx, player in enumerate(players):
            starting_x, starting_y = starting_positions[idx % len(starting_positions)]
            initial_state["players"][player] = {
                "position": [starting_x, starting_y],
                "direction": None,
                "moving": False,
                "speed": 2.0,  # Vitesse en unités par seconde
                "bombs": 1,
                "max_bombs": 1,
                "bomb_range": 2,
                "alive": True
            }
        await self.redis.set_game_state(room_id, initial_state)
        return initial_state

    def generate_initial_map(self):
        width = 15
        height = 15
        walls = []
        breakable_walls = []
        for x in range(width):
            for y in range(height):
                if x % 2 == 0 and y % 2 == 0:
                    walls.append([x, y])
                else:
                    if random.random() < 0.7:
                        # Laisser des espaces autour des positions de départ
                        if not ((x <= 2 and y <= 2) or (x >= width - 3 and y <= 2) or (x <=2 and y >= height - 3) or (x >= width -3 and y >= height -3)):
                            breakable_walls.append([x, y])
        return {
            "width": width,
            "height": height,
            "walls": walls,  # Murs incassables
            "breakable_walls": breakable_walls,  # Murs cassables
        }

    async def handle_game_action(self, room_id: str, username: str, action: dict):
        if not await self.redis.is_game_started(room_id):
            raise ValueError("Le jeu n'a pas encore commencé")

        game_state = await self.redis.get_game_state(room_id)
        updated_state = self.process_action(game_state, username, action)
        await self.redis.set_game_state(room_id, updated_state)
        return updated_state

    def process_action(self, game_state: dict, username: str, action: dict) -> dict:
        player = game_state["players"].get(username)
        if not player or not player["alive"]:
            return game_state

        if action["type"] == "start_move":
            direction = action.get("direction")
            if direction in ["up", "down", "left", "right"]:
                player["direction"] = direction
                player["moving"] = True

        elif action["type"] == "stop_move":
            player["moving"] = False

        elif action["type"] == "place_bomb":
            if player["bombs"] > 0:
                bomb_position = [
                    int(player["position"][0] + 0.5),
                    int(player["position"][1] + 0.5)
                ]
                # Vérifier s'il y a déjà une bombe à cette position
                if not any(bomb["position"] == bomb_position for bomb in game_state["bombs"]):
                    bomb = Bomb(position=bomb_position, owner=username, timer=2.0, range=player["bomb_range"])
                    game_state["bombs"].append(bomb.dict())
                    player["bombs"] -= 1

        # Ajoutez d'autres types d'actions selon les besoins

        return game_state

    async def game_loop(self, room_id: str):
        time_delta = 1 / 64.0  # 64 mises à jour par seconde (internes)
        send_interval = 1 / 30.0  # Envoyer l'état du jeu toutes les 30ms
        last_send_time = time.time()
        while await self.redis.is_game_started(room_id):
            game_state = await self.redis.get_game_state(room_id)

            # Mettre à jour les positions des joueurs
            for player_name, player in game_state["players"].items():
                if player["moving"] and player["direction"] and player["alive"]:
                    dx, dy = 0, 0
                    speed = player["speed"]
                    if player["direction"] == "up":
                        dy = -speed * time_delta
                    elif player["direction"] == "down":
                        dy = speed * time_delta
                    elif player["direction"] == "left":
                        dx = -speed * time_delta
                    elif player["direction"] == "right":
                        dx = speed * time_delta

                    new_x = player["position"][0] + dx
                    new_y = player["position"][1] + dy

                    if self.is_walkable(game_state, new_x, new_y):
                        player["position"][0] = new_x
                        player["position"][1] = new_y
                    else:
                        # Arrêter le mouvement en cas de collision
                        player["moving"] = False

            # Mettre à jour les bombes
            updated_bombs = []
            for bomb in game_state["bombs"]:
                bomb["timer"] -= time_delta
                if bomb["timer"] <= 0:
                    # Gérer l'explosion
                    self.handle_explosion(game_state, bomb)
                else:
                    updated_bombs.append(bomb)
            game_state["bombs"] = updated_bombs

            # Mettre à jour les explosions
            updated_explosions = []
            for explosion in game_state.get("explosions", []):
                explosion["timer"] -= time_delta
                if explosion["timer"] <= 0:
                    # Supprimer l'explosion
                    pass
                else:
                    updated_explosions.append(explosion)
            game_state["explosions"] = updated_explosions

            # Collecter les power-ups
            self.collect_powerups(game_state)




            await self.redis.set_game_state(room_id, game_state)

            current_time = time.time()
            if current_time - last_send_time >= send_interval:
                await self.manager.broadcast(room_id, {"event": "game_state", "state": game_state})
                last_send_time = current_time
            await asyncio.sleep(time_delta)  # Intervalle de mise à jour

    def is_walkable(self, game_state: dict, x: float, y: float) -> bool:
        map_data = game_state["map"]
        cell_x = int(x + 0.5)
        cell_y = int(y + 0.5)

        if cell_x < 0 or cell_x >= map_data["width"] or cell_y < 0 or cell_y >= map_data["height"]:
            return False

        # Vérifier les murs incassables
        walls_set = set(tuple(wall) for wall in map_data["walls"])
        if (cell_x, cell_y) in walls_set:
            return False

        # Vérifier les murs cassables
        breakable_walls_set = set(tuple(wall) for wall in map_data["breakable_walls"])
        if (cell_x, cell_y) in breakable_walls_set:
            return False

        # Vérifier les bombes
        bombs_set = set(tuple(bomb["position"]) for bomb in game_state["bombs"])
        if (cell_x, cell_y) in bombs_set:
            return False

        # Optionnel : Vérifier les autres joueurs
        # Vous pouvez décider si les joueurs peuvent se traverser ou non

        return True

    def handle_explosion(self, game_state: dict, bomb: dict):
        # Calculer les cellules affectées
        explosion_cells = self.get_explosion_cells(game_state, bomb)

        # Ajouter l'explosion à l'état du jeu
        explosion = {
            "positions": explosion_cells,
            "timer": 0.5  # L'explosion dure 0,5 seconde
        }
        game_state["explosions"].append(explosion)

        # Gérer les murs et les joueurs dans l'explosion
        self.apply_explosion_effects(game_state, explosion_cells)

        # Réinitialiser le nombre de bombes du propriétaire
        owner = bomb["owner"]
        if owner in game_state["players"]:
            game_state["players"][owner]["bombs"] += 1

    def get_explosion_cells(self, game_state: dict, bomb: dict):
        positions = []
        x, y = bomb["position"]
        positions.append([x, y])

        directions = [(-1,0), (1,0), (0,-1), (0,1)]  # Gauche, Droite, Haut, Bas

        for dx, dy in directions:
            for i in range(1, bomb.get("range", 2) + 1):
                nx = x + dx * i
                ny = y + dy * i

                if nx < 0 or nx >= game_state["map"]["width"] or ny < 0 or ny >= game_state["map"]["height"]:
                    break

                # Vérifier les murs
                if [nx, ny] in game_state["map"]["walls"]:
                    # Mur incassable bloque l'explosion
                    break

                positions.append([nx, ny])

                if [nx, ny] in game_state["map"]["breakable_walls"]:
                    # Mur cassable arrête l'explosion mais est détruit
                    break

                # Vérifier les bombes pour créer des réactions en chaîne
                for other_bomb in game_state["bombs"]:
                    if other_bomb["position"] == [nx, ny]:
                        other_bomb["timer"] = 0  # Détoner immédiatement
                        break

        return positions

    def apply_explosion_effects(self, game_state: dict, explosion_cells: List[List[int]]):
        # Supprimer les murs cassables
        breakable_walls = game_state["map"]["breakable_walls"]
        new_breakable_walls = []
        for wall in breakable_walls:
            if wall in explosion_cells:
                # Optionnel : laisser tomber un power-up
                if random.random() < 0.3:
                    powerup = self.create_random_powerup(wall)
                    game_state["powerups"].append(powerup.dict())
            else:
                new_breakable_walls.append(wall)
        game_state["map"]["breakable_walls"] = new_breakable_walls

        # Vérifier les joueurs touchés par l'explosion
        for player_name, player in game_state["players"].items():
            if player["alive"]:
                player_cell = [
                    int(player["position"][0] + 0.5),
                    int(player["position"][1] + 0.5)
                ]
                if player_cell in explosion_cells:
                    # Le joueur est touché par l'explosion
                    player["alive"] = False
                    player["moving"] = False
                    # Optionnel : gérer la réapparition ou la fin de partie

        # Supprimer les power-ups touchés par l'explosion
        new_powerups = []
        for powerup in game_state.get("powerups", []):
            if powerup["position"] not in explosion_cells:
                new_powerups.append(powerup)
        game_state["powerups"] = new_powerups

    def create_random_powerup(self, position: List[int]):
        # Sélectionner aléatoirement un type de power-up
        powerup_types = ["speed", "bomb_range", "bomb_count"]
        powerup_type = random.choice(powerup_types)
        return PowerUp(position=position, type=powerup_type)

    def collect_powerups(self, game_state: dict):
        for player_name, player in game_state["players"].items():
            if player["alive"]:
                player_cell = [
                    int(player["position"][0] + 0.5),
                    int(player["position"][1] + 0.5)
                ]
                for powerup in game_state.get("powerups", []):
                    if powerup["position"] == player_cell:
                        # Appliquer l'effet du power-up
                        self.apply_powerup_effect(player, powerup)
                        # Retirer le power-up de l'état du jeu
                        game_state["powerups"].remove(powerup)
                        break  # Supposons un power-up par cellule

    def apply_powerup_effect(self, player: dict, powerup: dict):
        if powerup["type"] == "speed":
            player["speed"] += 0.5  # Augmenter la vitesse
        elif powerup["type"] == "bomb_range":
            player["bomb_range"] += 1  # Augmenter la portée des bombes
        elif powerup["type"] == "bomb_count":
            player["max_bombs"] += 1  # Augmenter le nombre maximal de bombes
            player["bombs"] += 1

    # Ajoutez d'autres méthodes si nécessaire
