from typing import Literal
from pydantic import BaseModel


VideoStatus = Literal["queued", "uploaded", "processing", "error", "completed"]


class VideoProcessRequest(BaseModel):
    # caminho local ou URL (se for URL, seu service deve baixar antes)
    video_path: str
    fps: int = 1


class CreateVideoRequest(BaseModel):
    title: str
    storage_path: str | None = None
    original_url: str | None = None
    project_id: str | None = None
    status: Literal["queued", "uploaded"] = "queued"


class CreateVideoResponse(BaseModel):
    video_id: str
    project_id: str | None = None
    storage_path: str
    status: Literal["queued", "uploaded", "processing", "error"]


class VideoStatusResponse(BaseModel):
    video_id: str
    project_id: str | None = None
    storage_path: str | None = None
    status: VideoStatus
    signed_url: str | None = None
    error_detail: str | None = None
