# app/schemas/media.py
from pydantic import BaseModel, ConfigDict


class MediaUploadResponse(BaseModel):
    result: bool = True
    media_id: int