# app/services/room_service.py

from typing import List
from app.repositories.redis_repository import RedisRepository

class RoomService:
    def __init__(self, redis_repo: RedisRepository):
        self.redis = redis_repo

    async def create_room(self, room_id: str, creator: str):
        if await self.redis.room_exists(room_id):
            raise ValueError("La salle existe déjà")
        await self.redis.create_room(room_id, creator)

    async def list_rooms(self):
        keys = await self.redis.redis.keys("room:*")
        room_ids = [key.split(":")[1] for key in keys if len(key.split(":")) == 2]
        rooms = []
        for room_id in room_ids:
            creator = await self.redis.redis.hget(f"room:{room_id}", "creator")
            game_started = await self.redis.redis.hget(f"room:{room_id}", "game_started")
            players = await self.redis.get_room_players(room_id)
            rooms.append({
                "room_id": room_id,
                "creator": creator,
                "game_started": bool(int(game_started)),
                "players": list(players)
            })
        return rooms
