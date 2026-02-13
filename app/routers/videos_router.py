import os

from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from uuid import UUID
from uuid import uuid4
from app.services.supabase_client import get_supabase_client, get_service_role_client
from app.services.auth import get_current_user, get_access_token, get_user_id
from app.services.storage_service import normalize_storage_path, download_storage_file
from app.services.ffmpeg_service import has_audio_stream
from app.services.orchestrator import process_video_pipeline
from app.models.video_model import (
    CreateVideoRequest,
    CreateVideoResponse,
    VideoStatusResponse,
)

router = APIRouter(prefix="/videos")
ACCEPTED_INITIAL_STATUSES = {"queued", "uploaded"}
VIDEO_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "videos")
NO_AUDIO_UPLOAD_DETAIL = (
    "Video sem audio detectado. Envie um video com faixa de audio para gerar recomendacoes."
)


def _raise_for_supabase_error(exc: Exception) -> None:
    message = str(exc)
    if "42501" in message or "row-level security" in message or "permission" in message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RLS bloqueou a operacao em videos",
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


def _storage_remove_failed(result) -> bool:
    if result is None:
        return False
    if isinstance(result, dict):
        return bool(result.get("error"))
    return bool(getattr(result, "error", None))


def _extract_data(response):
    if isinstance(response, dict):
        return response.get("data")
    return getattr(response, "data", None)


def _remove_storage_path(path: str) -> None:
    if not path:
        return
    try:
        service_client = get_service_role_client()
        result = service_client.storage.from_(VIDEO_BUCKET).remove([path])
        if _storage_remove_failed(result):
            print(f"[videos] create.storage_cleanup_failed path={path} result={result}")
    except Exception as exc:
        print(f"[videos] create.storage_cleanup_error path={path} error={exc}")


def _validate_storage_audio_or_422(storage_path: str) -> None:
    local_path = None
    try:
        local_suffix = os.path.splitext(storage_path)[1] or ".mp4"
        local_path = download_storage_file(
            VIDEO_BUCKET,
            storage_path,
            suffix=local_suffix,
        )
        if not has_audio_stream(local_path):
            _remove_storage_path(storage_path)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=NO_AUDIO_UPLOAD_DETAIL,
            )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[videos] create.audio_validation_error storage_path={storage_path} error={exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao validar audio do video no Storage.",
        )
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


def _extract_error_detail(video: dict) -> str | None:
    if not isinstance(video, dict):
        return None
    for key in ("error_detail", "error_message", "last_error", "error"):
        value = video.get(key)
        if value:
            return str(value)
    if str(video.get("status", "")).lower() == "error":
        return "Falha no processamento do video. Consulte os logs do backend."
    return None


def _fetch_video_row(
    client,
    *,
    video_id: str,
    user_id: str,
):
    """
    Alguns ambientes retornam erro 204/Missing response no maybe_single.
    Faz fallback para select("*")+limit(1) quando isso ocorrer.
    """
    preferred_select = "id, project_id, storage_path, status, error_detail, error_message, last_error"
    try:
        response = (
            client.table("videos")
            .select(preferred_select)
            .eq("id", video_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return _extract_data(response)
    except Exception as exc:
        message = str(exc)
        if "Missing response" not in message and "Error 204" not in message:
            raise
        print(
            "[videos] status.fallback_query "
            f"video_id={video_id} user_id={user_id} reason={message}"
        )
        fallback_response = (
            client.table("videos")
            .select("*")
            .eq("id", video_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        data = _extract_data(fallback_response) or []
        if isinstance(data, list):
            return data[0] if data else None
        return data


def _create_response_from_row(video: dict) -> CreateVideoResponse:
    raw_status = str(video.get("status") or "").lower()
    contract_status = raw_status if raw_status in {"queued", "uploaded", "processing", "error"} else "queued"
    return CreateVideoResponse(
        video_id=str(video.get("id")),
        project_id=video.get("project_id"),
        storage_path=video.get("storage_path"),
        status=contract_status,
    )


@router.post("/", response_model=CreateVideoResponse)
def create_video(
    data: CreateVideoRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    token=Depends(get_access_token),
):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

        project_id = data.project_id
        if project_id:
            _validate_uuid(project_id, "project_id")
            project_resp = (
                client.table("projects")
                .select("id, user_id")
                .eq("id", project_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if not _extract_data(project_resp):
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

        storage_path = normalize_storage_path(data.storage_path, "videos")
        if not storage_path:
            storage_path = normalize_storage_path(data.original_url, "videos")

        if not storage_path:
            raise HTTPException(
                status_code=400,
                detail="storage_path ou original_url obrigatorio",
            )

        _validate_storage_audio_or_422(storage_path)

        initial_status = (
            data.status
            if data.status in ACCEPTED_INITIAL_STATUSES
            else "queued"
        )

        created_id = str(uuid4())
        payload = {
            "id": created_id,
            "user_id": user_id,
            "title": data.title,
            "status": initial_status,
            "storage_path": storage_path,
        }
        if data.original_url:
            payload["original_url"] = data.original_url
        if project_id:
            payload["project_id"] = project_id

        client.table("videos").insert(payload).execute()
        persisted_response = (
            client.table("videos")
            .select("id, project_id, storage_path, status")
            .eq("id", created_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        created = _extract_data(persisted_response)
        if not created:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Persistencia nao confirmada apos criar video.",
            )

        persisted_project_id = created.get("project_id")
        if project_id and persisted_project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Persistencia inconsistente: project_id divergente.",
            )

        print(
            "[videos] create.persisted "
            f"video_id={created_id} project_id={persisted_project_id} storage_path={created.get('storage_path')} status={created.get('status')}"
        )

        if initial_status in ACCEPTED_INITIAL_STATUSES:
            background_tasks.add_task(
                process_video_pipeline,
                video_id=created_id,
                storage_path=created.get("storage_path") or storage_path,
                access_token=token,
                user_id=user_id,
                project_id=persisted_project_id,
                initial_status=initial_status,
            )
            print(
                "[videos] create.enqueue "
                f"video_id={created_id} project_id={persisted_project_id} status={initial_status} action=background_pipeline"
            )

        return _create_response_from_row(created)
    except HTTPException:
        raise
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
        try:
            result = query.order("created_at", desc=True).execute()
        except Exception as order_exc:
            if "created_at" not in str(order_exc):
                raise
            result = query.order("id", desc=True).execute()
        data = _extract_data(result) or []
        print(
            "[videos] list "
            f"user_id={user_id} project_id={project_id} count={len(data)}"
        )
        return data
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase list_my_videos error:", repr(exc))
        _raise_for_supabase_error(exc)


@router.get("/{video_id}", response_model=VideoStatusResponse)
def get_video(video_id: str, user=Depends(get_current_user), token=Depends(get_access_token)):
    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")
        _validate_uuid(video_id, "video_id")

        video = _fetch_video_row(
            client,
            video_id=video_id,
            user_id=user_id,
        )
        if not video:
            raise HTTPException(status_code=404, detail="Video nao encontrado")

        raw_status = str(video.get("status") or "").lower()
        normalized_status = (
            raw_status
            if raw_status in {"queued", "uploaded", "processing", "error", "completed"}
            else "error"
        )
        payload = VideoStatusResponse(
            video_id=str(video.get("id")),
            project_id=video.get("project_id"),
            storage_path=video.get("storage_path"),
            status=normalized_status,
            error_detail=_extract_error_detail(video),
        )
        print(
            "[videos] status "
            f"video_id={payload.video_id} project_id={payload.project_id} status={payload.status} has_error_detail={bool(payload.error_detail)}"
        )
        return payload
    except HTTPException:
        raise
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
            .select("id, user_id, storage_path, original_url, proxy_url")
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
            raise HTTPException(status_code=404, detail="Video nao encontrado")

        storage_paths: list[str] = []
        if isinstance(video_data, dict):
            candidate_paths = [
                video_data.get("storage_path"),
                video_data.get("original_url"),
                video_data.get("proxy_url"),
            ]
        else:
            candidate_paths = [
                getattr(video_data, "storage_path", None),
                getattr(video_data, "original_url", None),
                getattr(video_data, "proxy_url", None),
            ]

        for value in candidate_paths:
            path = normalize_storage_path(value, "videos")
            if path:
                storage_paths.append(path)

        storage_paths = list(dict.fromkeys(storage_paths))

        if storage_paths:
            try:
                remove_result = client.storage.from_("videos").remove(storage_paths)
                if _storage_remove_failed(remove_result):
                    print(
                        "Storage remove failed: "
                        f"video_id={video_id} user_id={user_id} storage_paths={storage_paths} result={remove_result}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Falha ao remover arquivo no Storage",
                    )
            except HTTPException:
                raise
            except Exception as exc:
                print(
                    "Storage remove error: "
                    f"video_id={video_id} user_id={user_id} storage_paths={storage_paths} error={exc}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Falha ao remover arquivo no Storage",
                )
        else:
            print(
                "Storage path ausente, deletando apenas o registro: "
                f"video_id={video_id} user_id={user_id}"
            )

        client.table("transcriptions").delete().eq("video_id", video_id).execute()
        client.table("recommendations").delete().eq("video_id", video_id).execute()

        client.table("videos").delete().eq("id", video_id).eq("user_id", user_id).execute()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        print("Supabase delete_video error:", repr(exc))
        _raise_for_supabase_error(exc)
