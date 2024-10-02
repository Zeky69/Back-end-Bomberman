# app/repositories/redis_repository.py

import json
from typing import List
import redis.asyncio as redis
from app.config import settings

class RedisRepository:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )

    async def create_room(self, room_id: str, creator: str):
        await self.redis.hset(f"room:{room_id}", mapping={
            "creator": creator,
            "game_started": 0  # 0 pour False, 1 pour True
        })
        await self.redis.sadd(f"room:{room_id}:players", creator)

    async def add_player_to_room(self, room_id: str, username: str):
        await self.redis.sadd(f"room:{room_id}:players", username)

    async def remove_player_from_room(self, room_id: str, username: str):
        await self.redis.srem(f"room:{room_id}:players", username)
        if await self.redis.scard(f"room:{room_id}:players") == 0:
            await self.redis.delete(f"room:{room_id}", f"room:{room_id}:players", f"room:{room_id}:game_state")

    async def get_room_players(self, room_id: str) -> List[str]:
        return await self.redis.smembers(f"room:{room_id}:players")

    async def set_game_started(self, room_id: str):
        await self.redis.hset(f"room:{room_id}", "game_started", 1)  # 1 pour True

    async def is_game_started(self, room_id: str) -> bool:
        return (await self.redis.hget(f"room:{room_id}", "game_started")) == "1"

    async def set_game_state(self, room_id: str, state: dict):
        await self.redis.set(f"room:{room_id}:game_state", json.dumps(state))

    async def get_game_state(self, room_id: str) -> dict:
        state = await self.redis.get(f"room:{room_id}:game_state")
        return json.loads(state) if state else {}

    async def room_exists(self, room_id: str) -> bool:
        return await self.redis.exists(f"room:{room_id}")

    async def flushall(self):
        await self.redis.flushall()
