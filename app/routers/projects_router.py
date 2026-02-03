from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase_client import get_supabase_client
from app.services.auth import get_current_user, get_access_token

router = APIRouter(prefix="/projects")

def _raise_for_supabase_error(exc: Exception) -> None:
    message = str(exc)
    if "42501" in message or "row-level security policy" in message or "permission" in message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RLS policy blocked this action on 'projects'",
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable",
    )


@router.get("/")
def list_projects(user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        return (
            client.table("projects")
            .select("*")
            .eq("user_id", user.id)
            .execute()
            .data
        )
    except Exception as exc:
        print("Supabase list_projects error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.get("/{project_id}")
def get_project(project_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        return (
            client.table("projects")
            .select("*")
            .eq("id", project_id)
            .eq("user_id", user.id)
            .single()
            .execute()
            .data
        )
    except Exception as exc:
        print("Supabase get_project error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.post("/")
def create_project(payload: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        data = dict(payload)
        data["user_id"] = user.id
        response = client.table("projects").insert(data).execute()
        return {"status": "ok", "project": response.data}
    except Exception as exc:
        print("Supabase create_project error:", repr(exc))
        _raise_for_supabase_error(exc)
