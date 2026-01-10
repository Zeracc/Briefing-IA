from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
import uuid
import os
from app.services.dependencies import get_supabase_user


router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/files/upload")
async def upload_file(
    
    file: UploadFile = File(...),
    supabase=Depends(get_supabase_user),
    ):
    
    
    try:
        file_id = str(uuid.uuid4())
        extension = file.filename.split(".")[-1]
        filename = f"{file_id}.{extension}"

        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "id": file_id,
            "filename": filename,
            "path": file_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
