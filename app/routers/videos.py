# app/routers/videos.py
from fastapi import APIRouter, HTTPException
from app.models.video_model import VideoProcessRequest
from app.services import ffmpeg_service
from app.services.supabase_client import supabase
import os

router = APIRouter()


@router.post("/process")
def process_video(req: VideoProcessRequest):
    try:
        # 1) Opcional: persistir entrada no supabase (ex.: videos table)
        insert_resp = supabase.table("videos").insert({
            "user_id": None,
            "title": os.path.basename(req.video_path),
            "original_url": req.video_path,
            "status": "processing"
        }).execute()

        # 2) Executar processamento (pode demorar)
        proxy = ffmpeg_service.create_proxy(req.video_path)
        frames_pattern = ffmpeg_service.extract_frames(
            req.video_path, fps=req.fps)

        # 3) Atualizar registro no supabase com resultado
        # (ajuste a forma de recuperar id a partir de insert_resp.data)
        # Exemplo simplificado:
        # supabase.table("videos").update({"status": "done", "proxy_url": proxy}).eq("id", inserted_id).execute()

        return {"status": "ok", "proxy": proxy, "frames_pattern": frames_pattern}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
