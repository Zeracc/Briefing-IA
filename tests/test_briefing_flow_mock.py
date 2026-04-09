import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
# Adjust path to allow imports from app
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.video_model import VideoStatusResponse
# Import modules to test
# We need to mock dependencies before importing routers to avoid issues if they run code on import
# But routers usually just define functions/classes. 

class TestBriefingBackend(unittest.TestCase):

    @patch("app.routers.videos_router.get_supabase_client")
    @patch("app.routers.videos_router.get_user_id")
    def test_get_video_signed_url(self, mock_get_user_id, mock_get_client):
        # Setup
        from app.routers.videos_router import get_video
        
        mock_user = MagicMock()
        mock_token = "fake-token"
        mock_get_user_id.return_value = "user-123"
        
        # Mock Supabase Client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock DB response for get_video
        # The router uses .maybe_single().execute() logic
        mock_query_builder = MagicMock()
        mock_client.table.return_value = mock_query_builder
        mock_query_builder.select.return_value = mock_query_builder
        mock_query_builder.eq.return_value = mock_query_builder
        mock_query_builder.maybe_single.return_value = mock_query_builder
        
        # Mock database row
        video_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "project_id": None,
            "storage_path": "user-123/video.mp4",
            "status": "completed",
            "error_detail": None
        }
        
        # Response structure
        mock_response = MagicMock()
        mock_response.data = video_data
        # Handle _extract_data logic which checks dict or object
        # The router calls execute(), returns response
        mock_query_builder.execute.return_value = mock_response
        
        # Mock Storage create_signed_url
        # client.storage.from_().create_signed_url()
        mock_storage = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        # Return dict as per implementation expectation
        mock_storage.create_signed_url.return_value = {"signedURL": "https://signed.url/video.mp4"}

        # Execute
        result = get_video("123e4567-e89b-12d3-a456-426614174000", mock_user, mock_token)
        
        # Assert
        self.assertIsInstance(result, VideoStatusResponse)
        self.assertEqual(result.video_id, video_data["id"])
        self.assertEqual(result.signed_url, "https://signed.url/video.mp4")
        mock_storage.create_signed_url.assert_called_with("user-123/video.mp4", 3600)

    @patch("app.routers.recommendations_router.get_supabase_client")
    def test_get_recommendations_list(self, mock_get_client):
        # Setup
        from app.routers.recommendations_router import get_recommendations_list

        mock_user = MagicMock()
        mock_token = "fake-token"
        
        # Mock Client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock DB Query
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        
        # Mock Response
        recs_data = [
            {"timestamp_seconds": 10, "tag": "Intro", "description": "Scene 1"},
            {"timestamp_seconds": 20, "tag": "Middle", "description": "Scene 2"}
        ]
        mock_response = MagicMock()
        mock_response.data = recs_data
        mock_query.execute.return_value = mock_response
        
        # Execute
        result = get_recommendations_list("123e4567-e89b-12d3-a456-426614174000", mock_user, mock_token)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["tag"], "Intro")

if __name__ == "__main__":
    unittest.main()
