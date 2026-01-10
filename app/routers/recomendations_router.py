from fastapi import APIRouter, Depends, HTTPException, status
from app.services.dependencies import get_supabase_user
from app.services.auth import get_current_user
from app.services.permission import require_plan
from app.services.ai_services import gerar_recomendacoes

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post(
    "/generate",
    dependencies=[Depends(require_plan(["medium_ia", "master_ia"]))]
)
def generate(
    data: dict,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user),
):
    # 1️⃣ Valida payload
    video_id = data.get("video_id")
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'video_id' in body"
        )

    # 2️⃣ Busca transcrição DO USUÁRIO
    transcription = (
        supabase
        .table("transcriptions")
        .select("content")
        .eq("video_id", video_id)
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
        .data
    )

    if not transcription or "content" not in transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found for this video"
        )

    # 3️⃣ Chama IA
    try:
        resultado = gerar_recomendacoes(transcription["content"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {str(e)}"
        )

    if not isinstance(resultado, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid AI response format"
        )

    # 4️⃣ Salva recomendações vinculadas ao usuário
    supabase.table("recommendations").insert([
        {
            **item,
            "video_id": video_id,
            "user_id": user.id
        }
        for item in resultado
    ]).execute()

    return {
        "status": "ok",
        "recommendations": resultado
    }
