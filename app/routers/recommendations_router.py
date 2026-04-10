from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase_client import get_supabase_client, insert_as_user
from app.services.auth import get_current_user, get_access_token
from app.services.export_service import generate_ae_script
from app.services.briefing_engine_service import generate_video_briefing
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

    # 2. Envia para IA (Briefing Inteligente)
    try:
        briefing_result = generate_video_briefing(t["content"])
    except Exception as e:
        print("AI service error:", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI service error: {e}")

    # 3. Salva no banco (RLS como usuário)
    # 3.1 Briefing Consolidado
    briefing_payload = {
        "video_id": video_id,
        "content": briefing_result.model_dump()
    }
    b_result = insert_as_user("video_briefings", briefing_payload, token)
    if not b_result["ok"]:
        print(f"RLS insert video_briefings failed: {b_result['status']}, {b_result['body']}")
        raise HTTPException(status_code=b_result["status"], detail=b_result["body"])

    # 3.2 Recomendacoes Legadas (para Premiere/AE)
    legacy_payload = []
    for cut in briefing_result.cut_recommendations:
        legacy_payload.append({
            "video_id": video_id,
            "timestamp_seconds": cut.start,
            "tag": f"Corte ({cut.priority})",
            "description": cut.reason,
            "confidence": 1.0
        })
        
    for broll in briefing_result.broll_recommendations:
        legacy_payload.append({
            "video_id": video_id,
            "timestamp_seconds": broll.start,
            "tag": "B-roll",
            "description": f"Faixa {broll.time_range}: {broll.suggestion} (Motivo: {broll.reason})",
            "confidence": 1.0
        })
        
    if legacy_payload:
        rec_result = insert_as_user("recommendations", legacy_payload, token)
        if rec_result["ok"]:
            print("RLS insert as user (legacy recs): ok")

    return {"status": "ok", "briefing": briefing_result.model_dump()}


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


@router.get("/briefing/{video_id}")
def get_video_briefing(
    video_id: str,
    user=Depends(get_current_user),
    token=Depends(get_access_token)
):
    """Retorna o briefing estruturado salvo para o vídeo."""
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'video_id'")

    client = get_supabase_client(token)
    try:
        query = (
            client.table("video_briefings")
            .select("content")
            .eq("video_id", video_id)
            .maybe_single()
            .execute()
        )
        data = getattr(query, "data", None) if hasattr(query, "data") else (query.data if hasattr(query, "data") else None)
        
        if isinstance(query, dict) and "data" in query:
             data = query["data"]

        if not data:
            return None
            
        return data.get("content")
    except Exception as e:
        print("DB query error (video briefing):", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error querying briefing")


@router.get("/{video_id}/export-ae")
def export_ae_script(
    video_id: str,
    user=Depends(get_current_user),
    token=Depends(get_access_token)
):
    """Gera script .jsx para After Effects com marcadores."""
    # Reutiliza a logica de busca
    recs = get_recommendations_list(video_id, user, token)
    
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations found for this video")
        
    script_content = generate_ae_script(recs)
    
    return Response(
        content=script_content,
        media_type="application/javascript",
        headers={"Content-Disposition": f"attachment; filename=markers_{video_id}.jsx"}
    )

@router.get("/{video_id}/export-premiere")
def export_premiere_csv(
    video_id: str,
    user=Depends(get_current_user),
    token=Depends(get_access_token)
):
    """Gera CSV de marcadores para Adobe Premiere."""
    from app.services.export_service import generate_premiere_csv
    recs = get_recommendations_list(video_id, user, token)
    
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations found for this video")
        
    csv_content = generate_premiere_csv(recs)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=premiere_markers_{video_id}.csv"}
    )
