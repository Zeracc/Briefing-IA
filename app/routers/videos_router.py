from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase
from app.services.auth import get_current_user

router = APIRouter(prefix="/videos")

@router.post("/")
def create_video(data: dict, user=Depends(get_current_user)):
    payload = {
        "user_id": user.id,
        "title": data["title"],
        "original_url": data["original_url"],
        "status": "processing"
    }

    response = supabase.table("videos").insert(payload).execute()
    return {"status": "ok", "video": response.data}

@router.get("/")
def list_my_videos(user=Depends(get_current_user)):
    return (
        supabase.table("videos")
        .select("*")
        .eq("user_id", user.id)
        .execute()
        .data
    )

@router.get("/{video_id}")
def get_video(video_id: str, user=Depends(get_current_user)):
    return (
        supabase.table("videos")
        .select("*")
        .eq("id", video_id)
        .eq("user_id", user.id)
        .single()
        .execute()
        .data
    )
