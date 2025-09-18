# Загрузка одного или нескольких файлов медиа
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DomainValidation
from app.models import Media

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# при желании можно оставить пустым set(), чтобы разрешить всё
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "video/mp4"}


async def upload_medias(session: AsyncSession, *, files: List[UploadFile]) -> List[int]:
    """Сохранить одно или несколько медиафайлов и вернуть их id."""
    if not files:
        raise DomainValidation("no files provided")

    ids: list[int] = []
    for f in files:
        if not getattr(f, "filename", None):
            raise DomainValidation("file has no filename")

        if f.content_type and ALLOWED_MIME and f.content_type not in ALLOWED_MIME:
            raise DomainValidation(f"unsupported media type: {f.content_type}")

        name = f.filename or ""
        ext = Path(name).suffix or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext.lower()}"
        disk_path = MEDIA_DIR / unique_name

        # пишем поток на диск без загрузки всего в память
        with disk_path.open("wb") as out:
            shutil.copyfileobj(f.file, out)

        media = Media(path=f"media/{unique_name}")  # относительный путь по ТЗ
        session.add(media)
        await session.flush()  # получим media.id
        ids.append(media.id)

    return ids
