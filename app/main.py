from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rooms, websocket
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# Define allowed origins for CORS
origins = [
    "*",
]

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Origins that are allowed to communicate with the server
    allow_credentials=True,
    allow_methods=["*"],         # Allow all HTTP methods
    allow_headers=["*"],         # Allow all headers
)

# Include the routers
app.include_router(rooms.router)
app.include_router(websocket.router)

# Test client page (index.html)
@app.get("/", response_class=HTMLResponse)
async def get():
    # Define the path to index.html
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, media_type="text/html; charset=utf-8")
