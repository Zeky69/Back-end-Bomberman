# app/models/game_models.py

from pydantic import BaseModel
from typing import Dict, List

class PlayerState(BaseModel):
    position: List[int]
    bombs: int

class Bomb(BaseModel):
    position: List[int]
    owner: str
    timer: int

class GameState(BaseModel):
    players: Dict[str, PlayerState]
    map: Dict
    bombs: List[Bomb]
    explosions: List[Dict]
