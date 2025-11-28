from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import uuid
import os

router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
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
