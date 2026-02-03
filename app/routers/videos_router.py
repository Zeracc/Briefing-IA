from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.services.supabase_client import get_supabase_client
from app.services.auth import get_current_user, get_access_token

router = APIRouter(prefix="/videos")

def _raise_for_supabase_error(exc: Exception) -> None:
    message = str(exc)
    if "42501" in message or "row-level security" in message or "permission" in message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RLS bloqueou a operação em videos",
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable",
    )


def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
        return value
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} inválido (deve ser UUID)",
        )


@router.post("/")
def create_video(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        payload = {
            "user_id": user.id,
            "title": data["title"],
            "original_url": data["original_url"],
            "status": "processing",
        }

        response = client.table("videos").insert(payload).execute()
        return {"status": "ok", "video": response.data}
    except Exception as exc:
        print("Supabase create_video error:", repr(exc))
        _raise_for_supabase_error(exc)

@router.get("/")
def list_my_videos(
    user=Depends(get_current_user),
    token=Depends(get_access_token),
    project_id: str | None = None,
):
    try:
        client = get_supabase_client(token)
        query = client.table("videos").select("*").eq("user_id", user.id)
        if project_id:
            _validate_uuid(project_id, "project_id")
            query = query.eq("project_id", project_id)
        return query.execute().data
    except Exception as exc:
        print("Supabase list_my_videos error:", repr(exc))
        _raise_for_supabase_error(exc)

@router.get("/{video_id}")
def get_video(video_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        return (
            client.table("videos")
            .select("*")
            .eq("id", video_id)
            .eq("user_id", user.id)
            .single()
            .execute()
            .data
        )
    except Exception as exc:
        print("Supabase get_video error:", repr(exc))
        _raise_for_supabase_error(exc)
