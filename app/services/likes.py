# app/services/likes.py
# Лайк / анлайк твитов (строго по ТЗ, без лишних выборок)

# app/services/likes.py
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AlreadyExists, EntityNotFound
from app.models import Like, Tweet, User


async def like_tweet(session: AsyncSession, *, user_id: int, tweet_id: int) -> None:
    """
    Поставить лайк твиту.
    - Проверяем существование user и tweet.
    - Пытаемся вставить лайк.
    - Дубликат пары (user_id, tweet_id) конвертируем в AlreadyExists.
    """
    user = await session.get(User, user_id)
    tweet = await session.get(Tweet, tweet_id)
    if not user or not tweet:
        raise EntityNotFound("user or tweet not found")

    session.add(Like(user_id=user_id, tweet_id=tweet_id))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise AlreadyExists("like already exists")


async def unlike_tweet(session: AsyncSession, *, user_id: int, tweet_id: int) -> None:
    """
    Убрать лайк с твита.
    Идемпотентно: если записи нет — не ошибка.
    """
    await session.execute(delete(Like).where(Like.user_id == user_id, Like.tweet_id == tweet_id))
    await session.commit()
