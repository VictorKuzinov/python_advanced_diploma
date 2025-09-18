# app/services/likes.py
# Лайк / анлайк твитов
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AlreadyExists, EntityNotFound
from app.models import Like, Tweet, User


async def like_tweet(session: AsyncSession, *, user_id: int, tweet_id: int) -> None:
    """Поставить лайк твиту. Дубликат → AlreadyExists, отсутствие сущности → EntityNotFound."""
    user = await session.get(User, user_id)
    tweet = await session.get(Tweet, tweet_id)
    if not user or not tweet:
        raise EntityNotFound("user or tweet not found")
    async with session.begin_nested():
        session.add(Like(user_id=user_id, tweet_id=tweet_id))
        try:
            await session.flush()  # получим ошибку тут, если дубликат
        except IntegrityError:
            raise AlreadyExists("like already exists")


async def unlike_tweet(session: AsyncSession, *, user_id: int, tweet_id: int) -> None:
    """Снять лайк. Идемпотентно: если записи нет — не ошибка."""
    await session.execute(delete(Like).where(Like.user_id == user_id, Like.tweet_id == tweet_id))
