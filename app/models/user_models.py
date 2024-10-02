# app/models/user_models.py

from pydantic import BaseModel

class CreateRoomRequest(BaseModel):
    room_id: str
    username: str

class CreateRoomResponse(BaseModel):
    message: str
    room_id: str

class ListRoom(BaseModel):
    room_id: str
    creator: str
    game_started: bool
    players: list[str]
