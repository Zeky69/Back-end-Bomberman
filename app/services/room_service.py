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
        print("je suis dans list_rooms")
        try:
            keys = await self.redis.redis.keys("room:*")
            print("keys")

            room_ids = [key.split(":")[1] for key in keys if len(key.split(":")) == 2]
            print("room_ids")
            rooms = []
            for room_id in room_ids:
                print("room_id", room_id)
                creator = await self.redis.redis.hget(f"room:{room_id}", "creator")
                print("creator", creator)
                game_started = await self.redis.redis.hget(f"room:{room_id}", "game_started")
                print("game_started", game_started)
                players = await self.redis.get_room_players(room_id)
                print("players", players)
                rooms.append({
                    "room_id": room_id,
                    "creator": creator,
                    "game_started": bool(int(game_started)),
                    "players": list(players)
                })
            print("rooms", rooms)
            return rooms
        except Exception as e:
            print("il y a une erreur")

            print(e)
            return []
