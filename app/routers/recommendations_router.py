from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase_client import get_supabase_client, insert_as_user
from app.services.auth import get_current_user, get_access_token
from app.services.ai_services import gerar_recomendacoes
from app.services.export_service import generate_ae_script
from fastapi.responses import Response

router = APIRouter(prefix="/recommendations")


@router.post("/generate")
def generate(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    """Gera recomendaÃ§Ãµes a partir da transcriÃ§Ã£o do `video_id`.

    Body esperado: { "video_id": "..." }
    """
    video_id = data.get("video_id")
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'video_id' in body")

    client = get_supabase_client(token)

    # 1. Busca transcriÃ§Ã£o
    try:
        # use maybe_single() to avoid exception when 0 rows are returned
        query = (
            client.table("transcriptions")
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

    # 3. Salva no banco (RLS como usuÃ¡rio)
    payload = [{**item, "video_id": video_id} for item in resultado]
    result = insert_as_user("recommendations", payload, token)
    if result["ok"]:
        print("RLS insert as user: ok")
    else:
        print(f"RLS insert failed: {result['status']}, {result['body']}")
        raise HTTPException(status_code=result["status"], detail=result["body"])

    return {"status": "ok", "recommendations": resultado}


@router.get("/{video_id}")
def get_recommendations_list(
    video_id: str,
    user=Depends(get_current_user),
    token=Depends(get_access_token)
):
    """Retorna as recomendações salvas para o vídeo."""
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'video_id'")

    client = get_supabase_client(token)

    try:
        query = (
            client.table("recommendations")
            .select("*")
            .eq("video_id", video_id)
            .execute()
        )
        # Em algumas versoes do cliente Supabase, data pode estar em .data ou ser o retorno direto
        data = getattr(query, "data", []) if hasattr(query, "data") else (query.data if hasattr(query, "data") else [])
        
        # Se data for None ou nao iteravel
        if data is None:  
             data = []
             
        # Se query for um dict (postgrest response as dict)
        if isinstance(query, dict) and "data" in query:
             data = query["data"]
             
        return data
    except Exception as e:
        print("DB query error (recommendations list):", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error querying recommendations")


@router.get("/{video_id}/export-ae")
def export_ae_script(
    video_id: str,
    user=Depends(get_current_user),
    token=Depends(get_access_token)
):
    """Gera script .jsx para After Effects com marcadores."""
    # Reutiliza a lógica de busca
    recs = get_recommendations_list(video_id, user, token)
    
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations found for this video")
        
    script_content = generate_ae_script(recs)
    
    return Response(
        content=script_content,
        media_type="application/javascript",
        headers={"Content-Disposition": f"attachment; filename=markers_{video_id}.jsx"}
    )
