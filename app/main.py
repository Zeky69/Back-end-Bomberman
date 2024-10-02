# app/main.py

from fastapi import FastAPI
from app.routers import rooms, websocket
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# Inclure les routers
app.include_router(rooms.router)
app.include_router(websocket.router)

# Page client de test (index.html)
@app.get("/", response_class=HTMLResponse)
async def get():
    # Définir le chemin vers index.html
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, media_type="text/html; charset=utf-8")
