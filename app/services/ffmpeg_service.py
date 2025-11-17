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
