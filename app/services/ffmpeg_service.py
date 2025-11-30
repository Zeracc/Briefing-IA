# app/services/ffmpeg_service.py
import subprocess
import os
from typing import Tuple

FRAMES_DIR = os.path.join(os.path.dirname(
    __file__), "..", "..", "assets", "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)


def extract_frames(video_path: str, out_pattern: str = "frame_%04d.jpg", fps: int = 1) -> str:
    """
    Extrai frames do vídeo e retorna o caminho do pattern (ex: assets/frames/frame_%04d.jpg).
    """
    output_pattern = os.path.join(FRAMES_DIR, out_pattern)
    comando = [
        "ffmpeg",
        "-y",  # sobrescrever se necessário
        "-i", video_path,
        "-vf", f"fps={fps}",
        output_pattern
    ]
    subprocess.run(comando, check=True)
    return output_pattern


def create_proxy(video_path: str, output_name: str = None) -> str:
    if output_name is None:
        base = os.path.basename(video_path)
        output_name = f"proxy_{base}"
    output_path = os.path.join(FRAMES_DIR, output_name)
    comando = ["ffmpeg", "-y", "-i", video_path, "-c:v",
               "libx264", "-preset", "fast", "-crf", "28", output_path]
    subprocess.run(comando, check=True)
    return output_path

# Adapte as flags do ffmpeg conforme seu extract_frames.py original.


def extract_audio(video_path: str) -> str:
    """
    Extrai apenas o áudio do vídeo para enviar ao Whisper (formato mp3).
    Salva no mesmo diretório do vídeo original.
    """
    # Define nome do arquivo de saida (ex: video.mp4 -> video.mp3)
    audio_path = os.path.splitext(video_path)[0] + ".mp3"

    comando = [
        "ffmpeg",
        "-y",          # Sobrescrever se existir
        "-i", video_path,
        "-vn",         # Ignorar vídeo (Video None)
        "-acodec", "libmp3lame",  # Codec MP3
        "-q:a", "4",   # Qualidade média/boa
        audio_path
    ]

    # Roda o comando e lança erro se falhar
    subprocess.run(comando, check=True)

    return audio_path
