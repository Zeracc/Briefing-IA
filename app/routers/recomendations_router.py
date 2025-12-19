from fastapi import APIRouter, Depends, HTTPException, status
from app.services.dependencies import get_supabase_user
from app.services.auth import get_current_user
from app.services.ai_services import gerar_recomendacoes

router = APIRouter(prefix="/recommendations")


@router.post("/generate")
def generate(data: dict, 
             user=Depends(get_current_user),
             supabase=Depends(get_supabase_user)):
    """Gera recomendações a partir da transcrição do `video_id`.

    Body esperado: { "video_id": "..." }
    """
    video_id = data.get("video_id")
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'video_id' in body")

    # 1. Busca transcrição
    try:
        # use maybe_single() to avoid exception when 0 rows are returned
        query = (
            supabase.table("transcriptions")
            .select("*")
            .eq("video_id", video_id)
            .maybe_single()
            .execute()
        )
        t = getattr(query, "data", None)
    except Exception as e:
        print("DB query error:", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error querying transcriptions")

    if not t or not isinstance(t, dict) or "content" not in t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transcription not found for video_id {video_id}")

    # 2. Envia para IA
    try:
        resultado = gerar_recomendacoes(t["content"])
    except Exception as e:
        print("AI service error:", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI service error: {e}")

    if not isinstance(resultado, list):
        print("Invalid AI response format:", resultado)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid recommendations format returned by AI")

    # 3. Salva no banco
    try:
        supabase.table("recommendations").insert([
            {**item, "video_id": video_id} for item in resultado
        ]).execute()
    except Exception as e:
        print("DB insert error:", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inserting recommendations into database")

    return {"status": "ok", "recommendations": resultado}
