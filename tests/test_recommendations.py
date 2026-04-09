import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.auth import get_current_user, get_access_token

client = TestClient(app)

def override_get_current_user():
    return {"id": "test-user-id"}

def override_get_access_token():
    return "fake-token"

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_access_token] = override_get_access_token

@patch("app.routers.recommendations_router.get_supabase_client")
@patch("app.routers.recommendations_router.gerar_recomendacoes")
@patch("app.routers.recommendations_router.insert_as_user")
def test_generate_recommendations(mock_insert, mock_gerar_ai, mock_get_supabase):
    # Mock supabase to return a transcription
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    
    mock_query = MagicMock()
    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.maybe_single.return_value = mock_query
    
    mock_resp = MagicMock()
    mock_resp.data = {"content": "Olá, este é um vídeo teste sobre IA."}
    mock_query.execute.return_value = mock_resp
    
    # Mock AI Service simulate AI
    mock_gerar_ai.return_value = [
        {"timestamp_seconds": 10, "tag": "Corte", "description": "Remover silêncio"}
    ]
    
    # Mock DB insert
    mock_insert.return_value = {"ok": True, "status": 201, "body": {}}
    
    response = client.post("/api/recommendations/generate", json={"video_id": "fake-video-id"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["tag"] == "Corte"
