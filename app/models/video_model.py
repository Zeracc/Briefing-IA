# app/models/video_model.py
from pydantic import BaseModel


class VideoProcessRequest(BaseModel):
    # caminho local ou URL (se for URL, seu service deve baixar antes)
    video_path: str
    fps: int = 1
