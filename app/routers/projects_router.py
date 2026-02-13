from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.services.auth import get_access_token, get_current_user, get_user_id
from app.services.storage_service import normalize_storage_path
from app.services.supabase_client import get_supabase_client

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


def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
        return value
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} invalido (deve ser UUID)",
        )


def _extract_data(response):
    if isinstance(response, dict):
        return response.get("data")
    return getattr(response, "data", None)


def _storage_remove_failed(result) -> bool:
    if result is None:
        return False
    if isinstance(result, dict):
        return bool(result.get("error"))
    return bool(getattr(result, "error", None))


@router.get("/")
def list_projects(user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")
        return (
            client.table("projects")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase list_projects error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.get("/{project_id}")
def get_project(project_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")
        _validate_uuid(project_id, "project_id")
        return (
            client.table("projects")
            .select("*")
            .eq("id", project_id)
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase get_project error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.post("/")
def create_project(payload: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")
        data = dict(payload)
        data["user_id"] = user_id
        response = client.table("projects").insert(data).execute()
        return {"status": "ok", "project": response.data}
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase create_project error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.delete("/{project_id}")
def delete_project(project_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        _validate_uuid(project_id, "project_id")

        project_resp = (
            client.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        project_data = _extract_data(project_resp)
        if not project_data:
            raise HTTPException(status_code=404, detail="Projeto nao encontrado")

        videos_resp = (
            client.table("videos")
            .select("id, storage_path, original_url, proxy_url")
            .eq("project_id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        videos = _extract_data(videos_resp) or []

        storage_paths = set()
        video_ids = []
        for video in videos:
            if not isinstance(video, dict):
                continue

            video_id = video.get("id")
            if video_id:
                video_ids.append(str(video_id))

            for key in ("storage_path", "original_url", "proxy_url"):
                normalized = normalize_storage_path(video.get(key), "videos")
                if normalized:
                    storage_paths.add(normalized)

        if storage_paths:
            remove_result = client.storage.from_("videos").remove(list(storage_paths))
            if _storage_remove_failed(remove_result):
                print(
                    "[projects] delete.storage_failed "
                    f"project_id={project_id} user_id={user_id} storage_paths={list(storage_paths)} result={remove_result}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Falha ao remover arquivos do projeto no Storage",
                )

        for video_id in video_ids:
            client.table("recommendations").delete().eq("video_id", video_id).execute()
            client.table("transcriptions").delete().eq("video_id", video_id).execute()

        client.table("videos").delete().eq("project_id", project_id).eq("user_id", user_id).execute()
        client.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()

        print(
            "[projects] delete.done "
            f"project_id={project_id} user_id={user_id} videos_deleted={len(video_ids)} storage_deleted={len(storage_paths)}"
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase delete_project error:", repr(exc))
        _raise_for_supabase_error(exc)
