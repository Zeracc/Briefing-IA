import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.auth import get_current_user, get_access_token

client = TestClient(app)

def override_get_current_user():
    return {"id": "test-user-id", "email": "test@example.com"}

def override_get_access_token():
    return "fake-token"

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_access_token] = override_get_access_token

@patch("app.routers.projects_router.get_supabase_client")
@patch("app.routers.projects_router.get_user_id")
def test_list_projects(mock_get_user_id, mock_get_supabase):
    mock_get_user_id.return_value = "test-user-id"
    
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    
    mock_query = MagicMock()
    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    mock_resp = MagicMock()
    mock_resp.data = [{"id": "proj-1", "name": "Project 1"}]
    mock_query.execute.return_value = mock_resp
    
    response = client.get("/api/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["id"] == "proj-1"
