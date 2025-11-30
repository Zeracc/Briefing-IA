import os
import shutil
from app.services.ffmpeg_service import extract_audio, extract_frames
from app.services.ai_services import transcribe_audio, gerar_recomendacoes
from app.services.supabase_client import supabase


def process_video_pipeline(video_id: str, file_path: str):
    print(f"🔄 Iniciando processamento para vídeo: {video_id}")

    try:
        # 1. Atualizar status para 'processing'
        # Nota: Ajuste se sua tabela videos usar outra coluna para status
        supabase.table("videos").update(
            {"status": "processing"}).eq("id", video_id).execute()

        # 2. Extrair Áudio
        audio_path = extract_audio(file_path)
        print("✅ Áudio extraído.")

        # 3. Transcrever com Whisper
        transcription_data = transcribe_audio(audio_path)
        print("✅ Transcrição concluída.")

        segments_payload = []
        if hasattr(transcription_data, 'segments'):
            for segment in transcription_data.segments:
                # Extraímos manualmente para garantir que é JSON puro
                segments_payload.append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    # Adicione outros campos se precisar, mas esses são os principais
                })

        # 4. Salvar Transcrição no Banco
        supabase.table("transcriptions").insert({
            "video_id": video_id,
            "content": transcription_data.text,
            "segments": segments_payload,  # Agora é uma lista de dicts, não de objetos
            "language": transcription_data.language
        }).execute()

        # 5. Gerar Recomendações (IA Analisando o texto)
        recomendacoes = gerar_recomendacoes(transcription_data.text)

        # 6. Salvar Recomendações
        if recomendacoes:
            payload = []
            for rec in recomendacoes:
                payload.append({
                    "video_id": video_id,
                    "timestamp_seconds": rec.get("timestamp_seconds"),
                    "tag": rec.get("tag"),
                    "description": rec.get("description"),
                    "confidence": rec.get("confidence", 1.0)
                })
            supabase.table("recommendations").insert(payload).execute()
            print("✅ Recomendações salvas.")

        # 7. (Opcional) Extrair Frames para exibição no front
        # extract_frames(file_path)

        # 8. Finalizar
        supabase.table("videos").update(
            {"status": "completed"}).eq("id", video_id).execute()
        print(f"🏁 Processamento finalizado: {video_id}")

        # Limpeza de arquivos temporários (se desejar economizar espaço)
        # os.remove(audio_path)

    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        supabase.table("videos").update(
            {"status": "error"}).eq("id", video_id).execute()
