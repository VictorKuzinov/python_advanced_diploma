from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.routes.dependencies import get_current_user  # проверка API-Key
from app.schemas import MediaUploadResponse
from app.services.medias import upload_medias

router = APIRouter(prefix="/api/medias", tags=["medias"])


@router.post("", response_model=MediaUploadResponse)
async def upload_media_endpoint(
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
):
    """Загрузить одно или несколько изображений и вернуть id."""
    media_ids = await upload_medias(session, files=files)
    return {"result": True, "media_ids": media_ids}
