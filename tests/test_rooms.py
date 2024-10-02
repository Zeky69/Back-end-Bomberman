# tests/test_rooms.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.redis_repository import RedisRepository

client = TestClient(app)

@pytest.fixture(scope="module")
def redis_repo():
    return RedisRepository()

def test_create_room(redis_repo):
    response = client.post("/create_room", json={"room_id": "test_room", "username": "Alice"})
    assert response.status_code == 200
    assert response.json()["message"] == "Salle créée avec succès"
    assert response.json()["room_id"] == "test_room"

def test_create_existing_room(redis_repo):
    response = client.post("/create_room", json={"room_id": "test_room", "username": "Bob"})
    assert response.status_code == 400
    assert response.json()["detail"] == "La salle existe déjà"

def test_list_rooms(redis_repo):
    response = client.get("/list_rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert any(room["room_id"] == "test_room" for room in rooms)
