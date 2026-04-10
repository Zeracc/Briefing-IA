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
@patch("app.routers.recommendations_router.generate_video_briefing")
@patch("app.routers.recommendations_router.insert_as_user")
def test_generate_recommendations(mock_insert, mock_generate_video, mock_get_supabase):
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
    from app.models.video_briefing_model import VideoBriefingResult, CutRecommendation, BRollRecommendation
    
    mock_result = VideoBriefingResult(
        summary="Resumo",
        video_goal="Objetivo",
        target_audience="Devs",
        tone_analysis="Técnico",
        content_strengths=["Força"],
        content_weaknesses=["Fraqueza"],
        recommended_structure=[],
        highlight_moments=[],
        cut_recommendations=[
            CutRecommendation(start=10.0, end=15.0, reason="Corte simples", priority="low")
        ],
        broll_recommendations=[
            BRollRecommendation(time_range="0s", start=0.0, end=5.0, suggestion="Intro", reason="Abertura")
        ],
        caption_recommendations=[],
        cta_recommendation="Inscreva",
        title_suggestions=[],
        thumbnail_suggestions=[],
        editor_notes=[]
    )
    mock_generate_video.return_value = mock_result
    
    # Mock DB insert (we have two inserts now, brief and legacy recs)
    mock_insert.return_value = {"ok": True, "status": 201, "body": {}}
    
    response = client.post("/api/recommendations/generate", json={"video_id": "fake-video-id"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "briefing" in data
    assert len(data["briefing"]["cut_recommendations"]) == 1
    assert data["briefing"]["cut_recommendations"][0]["reason"] == "Corte simples"
