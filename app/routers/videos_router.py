from fastapi import APIRouter, Depends, HTTPException, status, Response
from uuid import UUID
from app.services.supabase_client import get_supabase_client
from app.services.auth import get_current_user, get_access_token, get_user_id

router = APIRouter(prefix="/videos")


def _raise_for_supabase_error(exc: Exception) -> None:
    message = str(exc)
    if "42501" in message or "row-level security" in message or "permission" in message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RLS bloqueou a operaÃ§Ã£o em videos",
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
            detail=f"{field_name} invÃ¡lido (deve ser UUID)",
        )


def _storage_path_from_value(value: str | None, bucket: str) -> str | None:
    if not value:
        return None
    normalized = value.strip()

    # URLs pÃºblicas do Supabase Storage
    public_marker = f"/storage/v1/object/public/{bucket}/"
    signed_marker = f"/storage/v1/object/sign/{bucket}/"
    if public_marker in normalized:
        return normalized.split(public_marker, 1)[1].split("?", 1)[0]
    if signed_marker in normalized:
        return normalized.split(signed_marker, 1)[1].split("?", 1)[0]

    # Caminho local (uploads/ ou caminho absoluto no Windows)
    if normalized.startswith("uploads") or "\\" in normalized or ":" in normalized:
        return None

    # Se jÃ¡ vier como path relativo ao bucket, retorna direto
    if normalized.startswith(f"{bucket}/"):
        return normalized[len(bucket) + 1 :]

    return normalized


@router.post("/")
def create_video(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        payload = {
            "user_id": user_id,
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
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        query = client.table("videos").select("*").eq("user_id", user_id)
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
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        return (
            client.table("videos")
            .select("*")
            .eq("id", video_id)
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception as exc:
        print("Supabase get_video error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.delete("/{video_id}")
def delete_video(video_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        _validate_uuid(video_id, "video_id")

        video_resp = (
            client.table("videos")
            .select("id, user_id, original_url, proxy_url")
            .eq("id", video_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        video_data = (
            video_resp.get("data")
            if isinstance(video_resp, dict)
            else getattr(video_resp, "data", None)
        )
        if not video_data:
            raise HTTPException(status_code=404, detail="Video nÃ£o encontrado")

        # Remove dependÃªncias (caso nÃ£o exista FK com ON DELETE CASCADE)
        client.table("transcriptions").delete().eq("video_id", video_id).execute()
        client.table("recommendations").delete().eq("video_id", video_id).execute()

        # Remove o prÃ³prio vÃ­deo
        client.table("videos").delete().eq("id", video_id).eq("user_id", user_id).execute()

        # Remove do Storage (bucket: videos), se aplicÃ¡vel
        paths = []
        for field in ("original_url", "proxy_url"):
            if isinstance(video_data, dict):
                value = video_data.get(field)
            else:
                value = getattr(video_data, field, None)
            path = _storage_path_from_value(value, "videos")
            if path:
                paths.append(path)
        if paths:
            try:
                client.storage.from_("videos").remove(paths)
            except Exception as exc:
                print("Storage remove error:", repr(exc))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase delete_video error:", repr(exc))
        _raise_for_supabase_error(exc)
