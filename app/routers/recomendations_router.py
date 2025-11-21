from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase
from app.services.auth import get_current_user
from app.services.ai_services import gerar_recomendacoes

router = APIRouter(prefix="/recommendations")

@router.post("/generate")
def generate(data: dict, user=Depends(get_current_user)):
    video_id = data["video_id"]

    # 1. Busca transcrição
    t = (
        supabase.table("transcriptions")
        .select("*")
        .eq("video_id", video_id)
        .single()
        .execute()
        .data
    )

    # 2. Envia para IA
    resultado = gerar_recomendacoes(t["content"])

    # 3. Salva no banco
    supabase.table("recommendations").insert([
        {**item, "video_id": video_id} for item in resultado
    ]).execute()

    return {"status": "ok", "recommendations": resultado}
