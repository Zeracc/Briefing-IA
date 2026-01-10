from fastapi import APIRouter, Depends, HTTPException, status
from app.services.dependencies import get_supabase_user
from app.services.auth import get_current_user

router = APIRouter(prefix="/videos", tags=["Videos"])

# =====================
# CREATE VIDEO
# =====================
@router.post("/")
def create_video(
    data: dict,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user),
):
    if not data.get("title") or not data.get("original_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing title or original_url"
        )

    payload = {
        "user_id": user.id,  # ✅ VINCULA AO USUÁRIO
        "title": data["title"],
        "original_url": data["original_url"],
        "status": "processing",
    }

    response = supabase.table("videos").insert(payload).execute()

    return {
        "status": "ok",
        "video": response.data[0]
    }


# =====================
# LIST MY VIDEOS
# =====================
@router.get("/")
def list_my_videos(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user),
):
    return (
        supabase
        .table("videos")
        .select("*")
        .eq("user_id", user.id)  # ✅ SOMENTE DO USUÁRIO
        .order("created_at", desc=True)
        .execute()
        .data
    )


# =====================
# GET SINGLE VIDEO
# =====================
@router.get("/{video_id}")
def get_video(
    video_id: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user),
):
    video = (
        supabase
        .table("videos")
        .select("*")
        .eq("id", video_id)
        .eq("user_id", user.id)  # ✅ BLOQUEIA ACESSO DE OUTROS
        .maybe_single()
        .execute()
        .data
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video
