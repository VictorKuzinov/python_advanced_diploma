# app/services/media.py
# Загрузка изображения для твита (минимум по ТЗ)
# app/services/medias.py
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DomainValidation
from app.models import Media

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


async def upload_media(session: AsyncSession, *, file: UploadFile) -> int:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise DomainValidation("only image/* files allowed")

    data = await file.read()
    if not data:
        raise DomainValidation("empty file")

    ext = Path(file.filename or "").suffix or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = MEDIA_DIR / unique_name
    with open(disk_path, "wb") as f:
        f.write(data)

    media = Media(path=f"media/{unique_name}")  # <- относительный путь
    session.add(media)
    await session.commit()
    await session.refresh(media)
    return media.id