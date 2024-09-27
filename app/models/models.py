# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import uuid4
import Player


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    x: float
    y: float



class Bomb(Entity):
    timer: int = 3  # Temps avant explosion en secondes
    owner_id: str


class Explosion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    x: int
    y: int
    direction: str  # 'up', 'down', 'left', 'right'
    duration: float = 1.0  # Durée de l'explosion en secondes


class GameState(BaseModel):
    grid: List[List[Optional[int]]]  # 0: vide, 1: mur destructible, 2: bombe, etc.
    players: Dict[str, Player]
    bombs: List[Bomb]
    explosions: List[Explosion] = Field(default_factory=list)


class Game(BaseModel):
    id: str
    room_id: str
    state: GameState
    is_active: bool = True

    def add_player(self, player: Player):
        self.state.players[player.id] = player

    def remove_player(self, player_id: str):
        del self.state.players[player_id]

    def add_bomb(self, bomb: Bomb):
        self.state.bombs.append(bomb)

    def remove_bomb(self, bomb: Bomb):
        self.state.bombs.remove(bomb)

    def add_explosion(self, explosion: Explosion):
        self.state.explosions.append(explosion)

    def remove_explosion(self, explosion: Explosion):
        self.state.explosions.remove(explosion)

    def get_tile(self, x: int, y: int) -> Optional[int]:
        if 0 <= x < len(self.state.grid) and 0 <= y < len(self.state.grid[0]):
            return self.state.grid[x][y]
        raise IndexError("Coordonnées de tuile hors limites")

    def set_tile(self, x: int, y: int, tile: int):
        if 0 <= x < len(self.state.grid) and 0 <= y < len(self.state.grid[0]):
            self.state.grid[x][y] = tile
        else:
            raise IndexError("Coordonnées de tuile hors limites")
