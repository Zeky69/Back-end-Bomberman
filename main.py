from fastapi import FastAPI
from app.routers import auth, room, game

app = FastAPI()

# Inclure les routers
app.include_router(auth.router, prefix="/auth")
app.include_router(room.router, prefix="/rooms")
app.include_router(game.router, prefix="/game")



