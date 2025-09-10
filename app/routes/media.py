from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.schemas import MediaUploadResponse
from app.services.medias import upload_media
from app.routes.dependencies import get_current_user  # проверка X-API-Key

router = APIRouter(prefix="/api/medias", tags=["medias"])


@router.post("/", response_model=MediaUploadResponse)
async def upload_media_endpoint(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
):
    """Загрузить изображение и вернуть его id (по ТЗ)."""
    media_id = await upload_media(session, file=file)
    return {"result": True, "media_id": media_id}