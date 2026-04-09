import sys
import os
from uuid import uuid4
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

@patch("app.routers.videos_router.get_supabase_client")
@patch("app.routers.videos_router.get_user_id")
def test_list_videos(mock_get_user_id, mock_get_supabase):
    mock_get_user_id.return_value = "test-user-id"
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    
    mock_query = MagicMock()
    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    
    mock_resp = MagicMock()
    mock_resp.data = [{"id": str(uuid4()), "title": "Vid 1"}]
    mock_query.execute.return_value = mock_resp
    
    response = client.get("/api/videos/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Vid 1"
