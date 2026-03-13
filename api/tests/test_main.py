import pytest
import sys
import os

# Magia: Ensina o Python a voltar uma pasta (..) para achar a API (main.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_acesso_sem_token_bloqueado():
    response = client.post("/videos/upload")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_rota_padrao_inexistente():
    response = client.get("/")
    assert response.status_code == 404
