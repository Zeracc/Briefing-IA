from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase
from app.services.auth import get_current_user

router = APIRouter(prefix="/transcriptions")

@router.post("/")
def create_transcription(data: dict, user=Depends(get_current_user)):
    return (
        supabase.table("transcriptions")
        .insert(data)
        .execute()
        .data
    )

@router.get("/{video_id}")
def get_transcription(video_id: str, user=Depends(get_current_user)):
    return (
        supabase.table("transcriptions")
        .select("*")
        .eq("video_id", video_id)
        .single()
        .execute()
        .data
    )
