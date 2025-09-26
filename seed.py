# seed.py
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models import User


async def seed() -> None:
    """Создать тестового пользователя для фронтенда (username/api_key = 'test')."""
    async with SessionLocal() as session:  # type: AsyncSession
        # Проверим, есть ли уже такой пользователь
        existing = await session.execute(
            User.__table__.select().where(User.username == "test")
        )
        user = existing.scalar_one_or_none()

        if not user:
            session.add(User(username="test", api_key="test"))
            await session.commit()
            print("✅ Пользователь 'test' создан.")
        else:
            print("ℹ️ Пользователь 'test' уже существует.")


if __name__ == "__main__":
    asyncio.run(seed())