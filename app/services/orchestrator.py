import os

from app.services.ffmpeg_service import (
    NoAudioStreamError,
    extract_audio,
    extract_frames,
    extract_snapshots,
)
from app.services.ai_services import transcribe_audio, gerar_recomendacoes
from app.services.supabase_client import get_supabase_client, insert_as_user
from app.services.storage_service import download_storage_file, normalize_storage_path

NO_AUDIO_ERROR_DETAIL = (
    "Video sem audio detectado. Envie um arquivo com faixa de audio para gerar recomendacoes."
)


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except Exception:
        return default


SNAPSHOT_INTERVAL_SECONDS = _read_int_env("VIDEO_SNAPSHOT_INTERVAL_SECONDS", 5)
SNAPSHOT_MAX_FRAMES = _read_int_env("VIDEO_SNAPSHOT_MAX_FRAMES", 8)


def _token_prefix(token: str | None) -> str:
    if not token:
        return "none"
    return f"{token[:8]}..."


def _extract_data(response):
    if isinstance(response, dict):
        return response.get("data")
    return getattr(response, "data", None)


def _update_video_status(
    client,
    video_id: str,
    status: str,
    error_detail: str | None = None,
):
    attempts = []
    if error_detail is not None:
        attempts.extend(
            [
                {"status": status, "error_detail": error_detail},
                {"status": status, "error_message": error_detail},
                {"status": status, "last_error": error_detail},
            ]
        )
    attempts.append({"status": status})

    last_error = None
    for payload in attempts:
        try:
            client.table("videos").update(payload).eq("id", video_id).execute()
            return
        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error


def process_video_pipeline(
    video_id: str,
    storage_path: str | None,
    access_token: str | None,
    user_id: str | None,
    project_id: str | None = None,
    initial_status: str | None = None,
    file_path: str | None = None,
):
    token_prefix = _token_prefix(access_token)
    print(
        "[videos] pipeline.start "
        f"video_id={video_id} project_id={project_id} initial_status={initial_status} token={token_prefix}"
    )

    if not access_token or not user_id:
        print(
            "[videos] pipeline.abort "
            f"video_id={video_id} reason=missing_jwt_or_user_id"
        )
        return

    client = get_supabase_client(access_token)

    try:
        # Verifica ownership do video antes de processar
        video_resp = (
            client.table("videos")
            .select("id, user_id, storage_path, original_url")
            .eq("id", video_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        video_data = _extract_data(video_resp)
        if not video_data:
            print(
                "[videos] pipeline.abort "
                f"video_id={video_id} reason=video_not_found_or_not_owned"
            )
            return

        resolved_storage_path = storage_path
        if isinstance(video_data, dict):
            if not resolved_storage_path:
                resolved_storage_path = normalize_storage_path(video_data.get("storage_path"), "videos")
            if not resolved_storage_path:
                resolved_storage_path = normalize_storage_path(video_data.get("original_url"), "videos")
        else:
            if not resolved_storage_path:
                resolved_storage_path = normalize_storage_path(getattr(video_data, "storage_path", None), "videos")
            if not resolved_storage_path:
                resolved_storage_path = normalize_storage_path(getattr(video_data, "original_url", None), "videos")

        local_video_path = None
        cleanup_paths: list[str] = []

        if resolved_storage_path:
            try:
                local_video_path = download_storage_file("videos", resolved_storage_path)
                cleanup_paths.append(local_video_path)
            except Exception as exc:
                print(
                    "[videos] pipeline.error "
                    f"video_id={video_id} user_id={user_id} storage_path={resolved_storage_path} error={exc}"
                )
                _update_video_status(
                    client,
                    video_id,
                    "error",
                    f"Falha no download do arquivo no Storage: {exc}",
                )
                return
        elif file_path and os.path.exists(file_path):
            local_video_path = file_path
        else:
            print(
                "[videos] pipeline.error "
                f"video_id={video_id} user_id={user_id}"
            )
            _update_video_status(
                client,
                video_id,
                "error",
                "storage_path ausente e arquivo local indisponivel.",
            )
            return

        # 1. Atualizar status para 'processing'
        _update_video_status(client, video_id, "processing")
        print(
            "[videos] pipeline.processing "
            f"video_id={video_id} project_id={project_id} storage_path={resolved_storage_path}"
        )

        # 2. Extrair Audio
        print(f"[videos] ffmpeg.start video_id={video_id} action=extract_audio")
        try:
            audio_path = extract_audio(local_video_path)
        except NoAudioStreamError:
            print(f"[videos] ffmpeg.no_audio video_id={video_id}")
            _update_video_status(
                client,
                video_id,
                "error",
                NO_AUDIO_ERROR_DETAIL,
            )
            return
        if local_video_path in cleanup_paths:
            cleanup_paths.append(audio_path)
        print(f"[videos] ffmpeg.done video_id={video_id} action=extract_audio")

        # 3. Transcrever com Whisper
        transcription_data = transcribe_audio(audio_path)
        print(f"[videos] transcription.done video_id={video_id}")

        segments_payload = []
        if hasattr(transcription_data, "segments"):
            for segment in transcription_data.segments:
                # Extraimos manualmente para garantir que e JSON puro
                segments_payload.append(
                    {
                        "id": segment.id,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                    }
                )

        # 4. Salvar Transcricao no Banco (RLS como usuario)
        insert_result = insert_as_user(
            "transcriptions",
            {
                "video_id": video_id,
                "content": transcription_data.text,
                "segments": segments_payload,
                "language": transcription_data.language,
            },
            access_token,
        )
        if insert_result["ok"]:
            print(f"[videos] transcription.persisted video_id={video_id}")
        else:
            print(
                "[videos] transcription.persist_error "
                f"video_id={video_id} status={insert_result['status']} body={insert_result['body']}"
            )
            _update_video_status(
                client,
                video_id,
                "error",
                "Falha ao persistir transcricao.",
            )
            return

        # 5. Extrair snapshots para contexto visual na IA.
        snapshot_paths: list[str] = []
        try:
            snapshot_paths = extract_snapshots(
                local_video_path,
                interval_seconds=SNAPSHOT_INTERVAL_SECONDS,
                max_frames=SNAPSHOT_MAX_FRAMES,
            )
            cleanup_paths.extend(snapshot_paths)
            print(
                "[videos] snapshots.done "
                f"video_id={video_id} count={len(snapshot_paths)} interval={SNAPSHOT_INTERVAL_SECONDS}s"
            )
        except Exception as snapshot_exc:
            print(f"[videos] snapshots.error video_id={video_id} error={snapshot_exc}")

        # 6. Gerar Recomendacoes Avançadas (Briefing Inteligente)
        from app.services.briefing_engine_service import generate_video_briefing
        print(f"[videos] briefing.start video_id={video_id}")
        
        # Formatar transcricao com timestamps para maior precisão da IA
        formatted_transcription = ""
        if hasattr(transcription_data, "segments") and transcription_data.segments:
            for seg in transcription_data.segments:
                start_sec = int(seg.start)
                end_sec = int(seg.end)
                start_fmt = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
                end_fmt = f"{end_sec // 60:02d}:{end_sec % 60:02d}"
                formatted_transcription += f"[{start_fmt} - {end_fmt}] {seg.text.strip()}\n"
        else:
            formatted_transcription = getattr(transcription_data, "text", "")

        briefing_result = generate_video_briefing(
            transcricao=formatted_transcription,
            frame_paths=snapshot_paths,
        )
        print(f"[videos] briefing.done_ia video_id={video_id}")

        # 7. Salvar Briefing consolidado (Nova Tabela)
        briefing_payload = {
            "video_id": video_id,
            "content": briefing_result.model_dump()
        }
        b_result = insert_as_user("video_briefings", briefing_payload, access_token)
        if b_result["ok"]:
             print(f"[videos] briefing.persisted video_id={video_id}")
        else:
             print(f"[videos] briefing.persist_error video_id={video_id} status={b_result['status']}")
             _update_video_status(client, video_id, "error", "Falha ao persistir briefing.")
             return

        # 7.1 Retrocompatibilidade: Extrair cortes e B-Rolls e salvar na tabela antiga (export Premiere/AE)
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
            rec_result = insert_as_user("recommendations", legacy_payload, access_token)
            if rec_result["ok"]:
                print(f"[videos] recommendations.persisted_legacy video_id={video_id}")
            else:
                print(f"[videos] recommendations.persist_error_legacy video_id={video_id} status={rec_result['status']} body={rec_result['body']}")
                # não daremos abort se apenas o legacy falhar

        # 8. (Opcional) Extrair Frames para exibicao no front
        # extract_frames(local_video_path)

        # 9. Finalizar
        _update_video_status(client, video_id, "completed")
        print(f"[videos] pipeline.done video_id={video_id} status=completed")

        for cleanup_path in cleanup_paths:
            try:
                if cleanup_path and os.path.exists(cleanup_path):
                    os.remove(cleanup_path)
            except Exception:
                pass

    except Exception as e:
        print(f"[videos] pipeline.error video_id={video_id} error={e}")
        try:
            _update_video_status(
                client,
                video_id,
                "error",
                f"Falha no pipeline: {e}",
            )
        except Exception as inner_exc:
            print(f"[videos] pipeline.error_status_failed video_id={video_id} error={inner_exc}")
