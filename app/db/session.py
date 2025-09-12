# Стандартная библиотека
# (здесь ничего не нужно)

# Сторонние пакеты
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# локальные пакеты
from app.config import settings

# создаём движок
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

# создаём фабрику сессий для async
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# зависимость для FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
