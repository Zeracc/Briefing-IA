from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Form
from uuid import UUID
import shutil
import uuid
import os
from typing import Optional

# Imports dos seus serviços
from app.services.auth import get_current_user, get_access_token
from app.services.orchestrator import process_video_pipeline
from app.services.supabase_client import get_supabase_client

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
        return value
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} inválido (deve ser UUID)",
        )


@router.post("/files/upload")
async def upload_file(
    # Permite rodar o processo sem travar o usuário
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    user=Depends(get_current_user),    # Garante que temos o usuário logado
    token=Depends(get_access_token),
):
    # Validação: verificar se arquivo foi enviado
    if not file or not file.filename:
        raise HTTPException(
            status_code=400, 
            detail="Nenhum arquivo foi fornecido. Envie um arquivo válido no campo 'file'."
        )
    
    try:
        client = get_supabase_client(token)

        # Se project_id foi fornecido, valida antes de salvar o arquivo
        if project_id:
            _validate_uuid(project_id, "project_id")
            project_resp = (
                client.table("projects")
                .select("id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
            )
            project_data = (
                project_resp.get("data")
                if isinstance(project_resp, dict)
                else getattr(project_resp, "data", None)
            )
            if not project_data:
                raise HTTPException(status_code=404, detail="Projeto não encontrado")

        # 1. Gerar nome único e definir caminho
        file_id = str(uuid.uuid4())
        extension = file.filename.split(".")[-1]
        filename = f"{file_id}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 2. Salvar o arquivo fisicamente na pasta uploads
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Registrar no Banco de Dados (Supabase) com status 'queued'
        # IMPORTANTE: A tabela 'videos' precisa existir e ter as colunas user_id e project_id (opcional)
        data = {
            "id": file_id,
            "user_id": user.id,  # Pega o ID do usuário autenticado
            "title": file.filename,
            "status": "queued",
            "original_url": file_path
        }
        
        # Se project_id foi fornecido, adiciona ao registro
        if project_id:
            data["project_id"] = project_id

        # Executa o insert no Supabase (com JWT do usuário)
        client.table("videos").insert(data).execute()

        # 4. Disparar o Orquestrador em Background
        # O FastAPI vai responder o return abaixo IMEDIATAMENTE,
        # e depois vai rodar essa função process_video_pipeline "nos bastidores"
        background_tasks.add_task(process_video_pipeline, file_id, file_path)

        return {
            "id": file_id,
            "filename": filename,
            "path": file_path,
            "status": "processing_started",
            "message": "Upload recebido! O vídeo está sendo processado.",
            "project_id": project_id  # Retorna se foi fornecido
        }

    except HTTPException:
        # Re-raise HTTPExceptions (como o erro de validação 400)
        raise
    except Exception as e:
        print(f"Erro interno no upload: {e}")  # Ajuda a debugar no terminal
        message = str(e)
        if "Project not found" in message or "P0001" in message:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        if "42501" in message or "row-level security" in message or "permission" in message:
            raise HTTPException(status_code=403, detail="RLS bloqueou a operação em videos")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar o upload. Tente novamente mais tarde.",
        )
