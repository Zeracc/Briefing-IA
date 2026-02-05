from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase_client import get_supabase_client, insert_as_user
from app.services.auth import get_current_user, get_access_token

router = APIRouter(prefix="/transcriptions")


@router.post("/")
def create_transcription(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    result = insert_as_user("transcriptions", data, token)
    if result["ok"]:
        print("RLS insert as user: ok")
        return result["body"]
    print(f"RLS insert failed: {result['status']}, {result['body']}")
    raise HTTPException(status_code=result["status"], detail=result["body"])


@router.get("/{video_id}")
def get_transcription(video_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    client = get_supabase_client(token)
    return (
        client.table("transcriptions")
        .select("*")
        .eq("video_id", video_id)
        .single()
        .execute()
        .data
    )
