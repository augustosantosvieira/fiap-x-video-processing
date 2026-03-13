import pytest
import sys
import os
from fastapi.testclient import TestClient

# Estas duas linhas mágicas forçam o Python a procurar os arquivos na pasta atual (api/)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app

client = TestClient(app)

def test_acesso_sem_token_bloqueado():
    """Testa se a API bloqueia uploads de usuários não logados (Erro 401)"""
    response = client.post("/videos/upload")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_rota_padrao_inexistente():
    """Testa se a API retorna 404 para rotas que não existem"""
    response = client.get("/")
    assert response.status_code == 404
