from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import shutil
import uuid
import os

# Imports dos seus serviços
from app.services.auth import get_current_user
from app.services.orchestrator import process_video_pipeline
# <--- Faltava importar o supabase
from app.services.supabase_client import supabase

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/files/upload")
async def upload_file(
    # Permite rodar o processo sem travar o usuário
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(get_current_user)    # Garante que temos o usuário logado
):
    try:
        # 1. Gerar nome único e definir caminho
        file_id = str(uuid.uuid4())
        extension = file.filename.split(".")[-1]
        filename = f"{file_id}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 2. Salvar o arquivo fisicamente na pasta uploads
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Registrar no Banco de Dados (Supabase) com status 'queued'
        # IMPORTANTE: A tabela 'videos' precisa existir e ter a coluna user_id
        data = {
            "id": file_id,
            "user_id": user.id,  # Pega o ID do usuário autenticado
            "title": file.filename,
            "status": "queued",
            "original_url": file_path
        }

        # Executa o insert no Supabase
        supabase.table("videos").insert(data).execute()

        # 4. Disparar o Orquestrador em Background
        # O FastAPI vai responder o return abaixo IMEDIATAMENTE,
        # e depois vai rodar essa função process_video_pipeline "nos bastidores"
        background_tasks.add_task(process_video_pipeline, file_id, file_path)

        return {
            "id": file_id,
            "filename": filename,
            "path": file_path,
            "status": "processing_started",
            "message": "Upload recebido! O vídeo está sendo processado."
        }

    except Exception as e:
        print(f"Erro no upload: {e}")  # Ajuda a debugar no terminal
        raise HTTPException(status_code=500, detail=str(e))
