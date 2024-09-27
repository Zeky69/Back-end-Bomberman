# routers/auth.py
from fastapi import APIRouter
from app.models.models import create_user

router = APIRouter()

@router.post("/login")
async def login(username: str):
    # Logique pour créer ou récupérer l'utilisateur
    user = create_user(username)
    return {"message": "Logged in", "user": user}
