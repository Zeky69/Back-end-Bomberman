# app/routers/rooms.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.user_models import CreateRoomRequest, CreateRoomResponse, ListRoom
from app.services.room_service import RoomService
from app.repositories.redis_repository import RedisRepository


router = APIRouter()

@router.post("/create_room", response_model=CreateRoomResponse)
async def create_room_endpoint(request: CreateRoomRequest,
                               room_service: RoomService = Depends(lambda: RoomService(RedisRepository()))):
    try:
        await room_service.create_room(request.room_id, request.username)
        return CreateRoomResponse(message="Salle créée avec succès", room_id=request.room_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list_rooms", response_model=List[ListRoom])
async def list_rooms_endpoint(room_service: RoomService = Depends(lambda: RoomService(RedisRepository()))):
    rooms = await room_service.list_rooms()
    return rooms


@router.post("/reset")
async def reset_redis(redis: RedisRepository = Depends()):
    await redis.flushall()  # Réinitialise toutes les données dans Redis
    return {"message": "Redis has been reset."}