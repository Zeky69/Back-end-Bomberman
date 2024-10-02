from typing import Optional, List
from uuid import uuid4

from fastapi import FastAPI

from app.models.game import Game
from app.models.game_state import GameState
from app.models.player import Player
from app.models.room import Room


def create_game(room_id: str, grid: List[List[Optional[int]]]) -> Game:
    return Game(id=str(uuid4()), room_id=room_id, state=GameState(grid=grid, players={}, bombs=[], explosions=[]))


def create_user(username: str) -> Player:
    return Player(
        id=str(uuid4()),
        username=username,
        x=1.0,
        y=1.0,
    )


def create_room(name: str, max_players: int = 4) -> Room:
    return Room(
        name=name,
        max_players=max_players,
    )


def get_game_manager(app: FastAPI):
    return app.state.game_manager
