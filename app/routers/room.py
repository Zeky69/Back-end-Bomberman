# routers/room.py
from fastapi import APIRouter, HTTPException
from app.models.models import create_room

router = APIRouter()
rooms = {}  # Dict pour stocker les rooms créées


@router.post("/rooms/")
async def create_room_endpoint(name: str, max_players: int = 4):
    room = create_room(name, max_players)
    rooms[room.id] = room
    return room


@router.get("/rooms/")
async def list_rooms():
    return list(rooms.values())


@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, username: str):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    room = rooms[room_id]
    if len(room.players) >= room.max_players:
        raise HTTPException(status_code=400, detail="Room is full")

    user = create_user(username)
    room.players.append(user)
    return room
