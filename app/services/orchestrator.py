from app.services.ffmpeg_service import extract_audio, extract_frames
from app.services.ai_services import transcribe_audio, gerar_recomendacoes
from app.services.supabase_client import get_supabase_client, insert_as_user


def _token_prefix(token: str | None) -> str:
    if not token:
        return "none"
    return f"{token[:8]}..."


def process_video_pipeline(video_id: str, file_path: str, access_token: str | None, user_id: str | None):
    token_prefix = _token_prefix(access_token)
    print(f"ðŸ”„ Iniciando processamento para vÃ­deo: {video_id} (token {token_prefix})")

    if not access_token or not user_id:
        print("âŒ Pipeline sem JWT/user_id â€” abortando para evitar bypass de RLS.")
        return

    client = get_supabase_client(access_token)

    try:
        # Verifica ownership do vÃ­deo antes de processar
        video_resp = (
            client.table("videos")
            .select("id, user_id")
            .eq("id", video_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        video_data = (
            video_resp.get("data")
            if isinstance(video_resp, dict)
            else getattr(video_resp, "data", None)
        )
        if not video_data:
            print("âŒ VÃ­deo nÃ£o pertence ao usuÃ¡rio ou nÃ£o encontrado. Abortando.")
            return

        # 1. Atualizar status para 'processing'
        client.table("videos").update({"status": "processing"}).eq("id", video_id).execute()

        # 2. Extrair Ãudio
        audio_path = extract_audio(file_path)
        print("âœ… Ãudio extraÃ­do.")

        # 3. Transcrever com Whisper
        transcription_data = transcribe_audio(audio_path)
        print("âœ… TranscriÃ§Ã£o concluÃ­da.")

        segments_payload = []
        if hasattr(transcription_data, "segments"):
            for segment in transcription_data.segments:
                # ExtraÃ­mos manualmente para garantir que Ã© JSON puro
                segments_payload.append(
                    {
                        "id": segment.id,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                    }
                )

        # 4. Salvar TranscriÃ§Ã£o no Banco (RLS como usuÃ¡rio)
        insert_result = insert_as_user(
            "transcriptions",
            {
                "video_id": video_id,
                "content": transcription_data.text,
                "segments": segments_payload,  # JSON puro
                "language": transcription_data.language,
            },
            access_token,
        )
        if insert_result["ok"]:
            print("RLS insert as user: ok")
        else:
            print(f"RLS insert failed: {insert_result['status']}, {insert_result['body']}")
            client.table("videos").update({"status": "error"}).eq("id", video_id).execute()
            return

        # 5. Gerar RecomendaÃ§Ãµes (IA Analisando o texto)
        recomendacoes = gerar_recomendacoes(transcription_data.text)

        # 6. Salvar RecomendaÃ§Ãµes (RLS como usuÃ¡rio)
        if recomendacoes:
            payload = []
            for rec in recomendacoes:
                payload.append(
                    {
                        "video_id": video_id,
                        "timestamp_seconds": rec.get("timestamp_seconds"),
                        "tag": rec.get("tag"),
                        "description": rec.get("description"),
                        "confidence": rec.get("confidence", 1.0),
                    }
                )
            rec_result = insert_as_user("recommendations", payload, access_token)
            if rec_result["ok"]:
                print("RLS insert as user: ok")
            else:
                print(f"RLS insert failed: {rec_result['status']}, {rec_result['body']}")
                client.table("videos").update({"status": "error"}).eq("id", video_id).execute()
                return
            print("âœ… RecomendaÃ§Ãµes salvas.")

        # 7. (Opcional) Extrair Frames para exibiÃ§Ã£o no front
        # extract_frames(file_path)

        # 8. Finalizar
        client.table("videos").update({"status": "completed"}).eq("id", video_id).execute()
        print(f"ðŸ Processamento finalizado: {video_id}")

        # Limpeza de arquivos temporÃ¡rios (se desejar economizar espaÃ§o)
        # os.remove(audio_path)

    except Exception as e:
        print(f"âŒ Erro no pipeline: {e}")
        try:
            client.table("videos").update({"status": "error"}).eq("id", video_id).execute()
        except Exception as inner_exc:
            print(f"Falha ao marcar status error: {inner_exc}")
