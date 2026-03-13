from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_upload_sem_token_deve_falhar():
    response = client.post("/videos/upload")
    assert response.status_code == 401

def test_login_valido():
    response = client.post("/token", data={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
