# services/game_service.py
import asyncio
from app.models.models import Game, Bomb, Explosion, Player
from typing import Dict
import math
import time

MOVEMENT_SPEED = 2.0  # Vitesse de déplacement en cases par seconde

async def game_loop(game: Game):
    while game.is_active:
        start_time = time.time()
        update_players(game)
        await broadcast_game_state(game)
        elapsed = time.time() - start_time
        await asyncio.sleep(max(0, 1/60 - elapsed))  # 60 mises à jour par seconde

def update_players(game: Game):
    for player_id, player in game.state.players.items():
        if player.moving_direction:
            dx, dy = direction_to_delta(player.moving_direction)
            new_x = player.x + dx * MOVEMENT_SPEED / 60
            new_y = player.y + dy * MOVEMENT_SPEED / 60

            # Vérifier les collisions
            if not is_collision(game, new_x, new_y):
                player.x = new_x
                player.y = new_y
            else:
                player.moving_direction = None  # Arrêter le déplacement en cas de collision

def direction_to_delta(direction: str) -> tuple:
    deltas = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
    }
    return deltas.get(direction, (0, 0))

def is_collision(game: Game, x: float, y: float) -> bool:
    tile_x = int(math.floor(x))
    tile_y = int(math.floor(y))
    if game.state.get_tile(tile_x, tile_y) == 1:  # 1 représente un mur destructible
        return True
    # Ajouter d'autres vérifications de collision si nécessaire (autres joueurs, bombes, etc.)
    return False

async def broadcast_game_state(game: Game):
    for connection in game.connections:
        await connection.send_json(game.state.dict())



async def handle_bomb(game: Game, bomb: Bomb):
    await asyncio.sleep(bomb.timer)  # Attendre que la bombe explose
    explode_bomb(game, bomb)

def explode_bomb(game: Game, bomb: Bomb):
    explosion_range = 2
    x, y = bomb.x, bomb.y
    directions = ['up', 'down', 'left', 'right']

    for direction in directions:
        for distance in range(1, explosion_range + 1):
            if direction == 'up':
                nx, ny = x, y - distance
            elif direction == 'down':
                nx, ny = x, y + distance
            elif direction == 'left':
                nx, ny = x - distance, y
            elif direction == 'right':
                nx, ny = x + distance, y

            if 0 <= nx < len(game.state.grid) and 0 <= ny < len(game.state.grid[0]):
                if game.state.get_tile(nx, ny) == 1:
                    game.state.set_tile(nx, ny, 0)  # Détruire le mur
                    break  # L'explosion s'arrête ici
                elif game.state.get_tile(nx, ny) == 0:
                    explosion = Explosion(x=nx, y=ny, direction=direction)
                    game.add_explosion(explosion)
                    asyncio.create_task(handle_explosion(game, explosion))
            else:
                break  # Hors limites

    game.remove_bomb(bomb)
    asyncio.create_task(broadcast_game_state(game))

async def handle_explosion(game: Game, explosion: Explosion):
    await asyncio.sleep(explosion.duration)  # Durée de l'explosion
    game.remove_explosion(explosion)
    await broadcast_game_state(game)

def place_bomb(game: Game, player_id: str, x: float, y: float):
    tile_x = int(math.floor(x))
    tile_y = int(math.floor(y))
    for bomb in game.state.bombs:
        if bomb.x == tile_x and bomb.y == tile_y:
            return  # Ne pas placer de bombe supplémentaire

    bomb = Bomb(x=tile_x, y=tile_y, owner_id=player_id)
    game.add_bomb(bomb)
    game.state.set_tile(tile_x, tile_y, 2)  # 2 représente une bombe
    asyncio.create_task(handle_bomb(game, bomb))
