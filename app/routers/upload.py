from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Form
from uuid import UUID
import uuid
import os
import tempfile
from typing import Optional

from app.services.auth import get_current_user, get_access_token, get_user_id
from app.services.orchestrator import process_video_pipeline
from app.services.supabase_client import get_supabase_client, get_service_role_client
from app.services.ffmpeg_service import has_audio_stream
from app.models.video_model import CreateVideoResponse

router = APIRouter()

UPLOAD_MAX_SIZE_MB = int(os.getenv("UPLOAD_MAX_SIZE_MB", "200"))
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "videos")
NO_AUDIO_UPLOAD_DETAIL = (
    "Video sem audio detectado. Envie um video com faixa de audio para gerar recomendacoes."
)


def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
        return value
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} invalido (deve ser UUID)",
        )


@router.post("/files/upload", deprecated=True)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    user=Depends(get_current_user),
    token=Depends(get_access_token),
) -> CreateVideoResponse:
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo foi fornecido. Envie um arquivo valido no campo 'file'.",
        )

    try:
        client = get_supabase_client(token)
        user_id = get_user_id(user)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

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
            project_data = (
                project_resp.get("data")
                if isinstance(project_resp, dict)
                else getattr(project_resp, "data", None)
            )
            if not project_data:
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

        # Tamanho maximo
        file.file.seek(0, os.SEEK_END)
        size_bytes = file.file.tell()
        file.file.seek(0)
        max_bytes = UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo excede o limite de {UPLOAD_MAX_SIZE_MB} MB",
            )

        file.file.seek(0)
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Arquivo vazio.")

        local_temp = None
        try:
            extension = os.path.splitext(file.filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as handle:
                handle.write(file_bytes)
                local_temp = handle.name

            if not has_audio_stream(local_temp):
                raise HTTPException(
                    status_code=422,
                    detail=NO_AUDIO_UPLOAD_DETAIL,
                )
        finally:
            if local_temp and os.path.exists(local_temp):
                try:
                    os.remove(local_temp)
                except Exception:
                    pass

        file_id = str(uuid.uuid4())
        extension = file.filename.split(".")[-1]
        filename = f"{file_id}.{extension}"
        storage_path = f"{user_id}/{filename}"

        service_client = get_service_role_client()
        try:
            service_client.storage.from_(STORAGE_BUCKET).upload(
                storage_path,
                file_bytes,
                {"content-type": file.content_type or "application/octet-stream"},
            )
        except Exception as exc:
            print(f"Storage upload error: video_id={file_id} user_id={user_id} path={storage_path} error={exc}")
            raise HTTPException(
                status_code=502,
                detail="Falha ao enviar arquivo para o Storage",
            )

        data = {
            "id": file_id,
            "user_id": user_id,
            "title": file.filename,
            "status": "queued",
            "storage_path": storage_path,
            "original_url": storage_path,
        }

        if project_id:
            data["project_id"] = project_id

        client.table("videos").insert(data).execute()
        persisted_response = (
            client.table("videos")
            .select("id, project_id, storage_path, status")
            .eq("id", file_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        created = (
            persisted_response.get("data")
            if isinstance(persisted_response, dict)
            else getattr(persisted_response, "data", None)
        )
        if not created or not created.get("id"):
            raise HTTPException(
                status_code=503,
                detail="Falha ao persistir registro do video apos upload.",
            )

        persisted_project_id = created.get("project_id")
        print(
            "[videos] legacy_upload.persisted "
            f"video_id={created.get('id')} project_id={persisted_project_id} storage_path={created.get('storage_path')} status={created.get('status')}"
        )

        background_tasks.add_task(
            process_video_pipeline,
            video_id=created.get("id"),
            storage_path=created.get("storage_path") or storage_path,
            access_token=token,
            user_id=user_id,
            project_id=persisted_project_id,
            initial_status=created.get("status"),
        )
        print(
            "[videos] legacy_upload.enqueue "
            f"video_id={created.get('id')} project_id={persisted_project_id} status={created.get('status')} action=background_pipeline"
        )

        raw_status = str(created.get("status") or "").lower()
        contract_status = (
            raw_status
            if raw_status in {"queued", "uploaded", "processing", "error"}
            else "queued"
        )
        return CreateVideoResponse(
            video_id=str(created.get("id")),
            project_id=persisted_project_id,
            storage_path=created.get("storage_path") or storage_path,
            status=contract_status,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro interno no upload: {e}")
        message = str(e)
        if "Project not found" in message or "P0001" in message:
            raise HTTPException(status_code=404, detail="Projeto nao encontrado")
        if "42501" in message or "row-level security" in message or "permission" in message:
            raise HTTPException(status_code=403, detail="RLS bloqueou a operacao em videos")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar o upload. Tente novamente mais tarde.",
        )
