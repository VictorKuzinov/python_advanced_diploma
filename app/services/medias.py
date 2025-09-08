# app/services/media.py
# Загрузка изображения для твита (минимум по ТЗ)

from sqlalchemy.ext.asyncio import AsyncSession

from models import Media

async def upload_media(
    session: AsyncSession, *, filename: str | None = None, data_bytes: bytes | None = None
) -> int:
    """
    Минимум по ТЗ: создаём запись Media и возвращаем её id.
    Файл физически не сохраняем.
    """
    media = Media()          # только id + created_at
    session.add(media)
    await session.commit()
    await session.refresh(media)
    return media.id