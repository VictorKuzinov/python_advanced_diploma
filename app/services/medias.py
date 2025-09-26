# Загрузка одного файла медиа
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DomainValidation
from app.models import Media

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "video/mp4", "image/x-icon"}


async def upload_media(session: AsyncSession, *, file: UploadFile) -> int:
    """Сохранить ОДИН медиафайл и вернуть его id (контракт ТЗ)."""
    if not getattr(file, "filename", None):
        raise DomainValidation("file has no filename")

    if file.content_type and ALLOWED_MIME and file.content_type not in ALLOWED_MIME:
        raise DomainValidation(f"unsupported media type: {file.content_type}")

    name = file.filename or ""
    ext = (Path(name).suffix or ".bin").lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = MEDIA_DIR / unique_name

    # стриминговая запись на диск (без загрузки всего файла в память)
    with disk_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # если файл пустой — удаляем и кидаем доменную ошибку
    if disk_path.stat().st_size == 0:
        try:
            disk_path.unlink(missing_ok=True)
        finally:
            raise DomainValidation("empty file")

    media = Media(path=f"media/{unique_name}")
    session.add(media)
    await session.flush()  # получим media.id
    return media.id
