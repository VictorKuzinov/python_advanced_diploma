from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.routes.dependencies import get_current_user  # проверка API-Key
from app.schemas import MediaUploadResponse
from app.services.medias import upload_media

router = APIRouter(prefix="/api/medias", tags=["medias"])


@router.post(
    "",
    response_model=MediaUploadResponse,
    summary="Загрузить медиафайл",
    description="Принимает **один файл** (PNG/JPG/ICO) и возвращает его ID. "
    "Файл сохраняется в `media/`, в ответе приходит `media_id`.",
)
async def upload_media_endpoint(
    file: UploadFile = File(..., description="Файл PNG/JPG для загрузки"),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> MediaUploadResponse:  # <-- вот тут аннотация
    """Эндпоинт загрузки одного файла (PNG/JPG)."""
    media_id = await upload_media(session, file=file)
    return MediaUploadResponse(result=True, media_id=media_id)
