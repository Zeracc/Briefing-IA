import os
import shutil
import subprocess
import uuid

FRAMES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "frames")
SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "snapshots")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)


class NoAudioStreamError(RuntimeError):
    """Raised when the video has no audio track."""


def _require_binary(binary_name: str) -> None:
    if shutil.which(binary_name):
        return
    raise RuntimeError(f"{binary_name} nao encontrado no PATH.")


def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode == 0:
        return process
    stderr = (process.stderr or "").strip()
    stdout = (process.stdout or "").strip()
    raise RuntimeError(
        f"Comando falhou (code={process.returncode}): {' '.join(command)} | stderr={stderr} | stdout={stdout}"
    )


def has_audio_stream(video_path: str) -> bool:
    _require_binary("ffprobe")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "csv=p=0",
        video_path,
    ]
    result = _run_command(command)
    return bool((result.stdout or "").strip())


def extract_frames(video_path: str, out_pattern: str = "frame_%04d.jpg", fps: int = 1) -> str:
    output_pattern = os.path.join(FRAMES_DIR, out_pattern)
    _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps={fps}",
            output_pattern,
        ]
    )
    return output_pattern


def extract_snapshots(
    video_path: str,
    interval_seconds: int = 12,
    max_frames: int = 8,
) -> list[str]:
    _require_binary("ffmpeg")
    safe_interval = max(1, int(interval_seconds))
    safe_max_frames = max(1, int(max_frames))
    run_id = uuid.uuid4().hex[:10]
    snapshot_dir = os.path.join(SNAPSHOTS_DIR, run_id)
    os.makedirs(snapshot_dir, exist_ok=True)

    output_pattern = os.path.join(snapshot_dir, "snapshot_%03d.jpg")
    _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps=1/{safe_interval},scale=960:-2",
            "-frames:v",
            str(safe_max_frames),
            output_pattern,
        ]
    )

    snapshots = sorted(
        os.path.join(snapshot_dir, name)
        for name in os.listdir(snapshot_dir)
        if name.lower().endswith(".jpg")
    )

    if snapshots:
        return snapshots

    # Fallback: pelo menos 1 frame para contexto visual.
    fallback_path = os.path.join(snapshot_dir, "snapshot_000.jpg")
    _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "3",
            fallback_path,
        ]
    )
    return [fallback_path] if os.path.exists(fallback_path) else []


def create_proxy(video_path: str, output_name: str | None = None) -> str:
    if output_name is None:
        base = os.path.basename(video_path)
        output_name = f"proxy_{base}"
    output_path = os.path.join(FRAMES_DIR, output_name)
    _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "28",
            output_path,
        ]
    )
    return output_path


def extract_audio(video_path: str) -> str:
    if not has_audio_stream(video_path):
        raise NoAudioStreamError("VIDEO_WITHOUT_AUDIO")

    audio_path = os.path.splitext(video_path)[0] + ".mp3"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "4",
        audio_path,
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        stderr = (process.stderr or "").lower()
        if "does not contain any stream" in stderr or "stream map 'a'" in stderr:
            raise NoAudioStreamError("VIDEO_WITHOUT_AUDIO")
        raise RuntimeError(
            f"Falha ao extrair audio com ffmpeg (code={process.returncode}): {process.stderr}"
        )

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise NoAudioStreamError("VIDEO_WITHOUT_AUDIO")

    return audio_path
