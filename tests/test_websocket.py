# tests/test_websocket.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_websocket_connection():
    with client.websocket_connect("/ws/test_room/Alice") as websocket:
        data = websocket.receive_json()
        assert data["error"] == "Salle inexistante"

def test_websocket_after_room_creation():
    # Créez une salle
    response = client.post("/create_room", json={"room_id": "test_room", "username": "Alice"})
    assert response.status_code == 200

    # Connectez-vous via WebSocket
    with client.websocket_connect("/ws/test_room/Alice") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "player_joined"
        assert data["username"] == "Alice"
        assert "Alice" in data["players"]
