# app/services/tweets.py
# CRUD и бизнес-логика для твитов строго по ТЗ
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import DomainValidation, EntityNotFound, ForbiddenAction
from app.models import Follow, Like, Media, Tweet, User
from app.schemas import LikeUser, TweetOut, UserPublic


# -------------------- Вспомогательные функции --------------------
def _user_public(u: User) -> UserPublic:
    # username → name через алиасы pydantic
    return UserPublic(id=u.id, username=u.username)


async def _fetch_likers(session: AsyncSession, tweet_id: int) -> List[User]:
    q = (
        select(User)
        .join(Like, Like.user_id == User.id)
        .where(Like.tweet_id == tweet_id)
        .order_by(User.username.asc())
    )
    return list((await session.execute(q)).scalars().all())


def _tweet_to_dto(t: Tweet, *, likers: List[User]) -> TweetOut:
    return TweetOut(
        id=t.id,
        content=t.content,
        attachments=[m.path for m in t.attachments],
        author=_user_public(t.author),  # <<< ТОЛЬКО {id, name}
        likes=[LikeUser(user_id=u.id, name=u.username) for u in likers],
    )


# -------------------- Публичные функции сервиса --------------------
async def create_tweet(
    session: AsyncSession,
    *,
    author_id: int,
    content: str,
    media_ids: List[int] | None = None,
) -> TweetOut:
    # Валидация
    text = (content or "").strip()
    if not text:
        raise DomainValidation("tweet content cannot be empty")
    if len(text) > 280:
        raise DomainValidation("tweet content must be ≤ 280 characters")

    # Автор
    author = (
        await session.execute(select(User).where(User.id == author_id).limit(1))
    ).scalar_one_or_none()
    if not author:
        raise EntityNotFound("author not found")

    # Медиа
    media_objs: List[Media] = []
    ids = list(dict.fromkeys(media_ids or []))
    if ids:
        res = await session.execute(select(Media).where(Media.id.in_(ids)))
        media_objs = list(res.scalars().all())
        if len(media_objs) != len(ids):
            raise EntityNotFound("one or more media not found")

    # Создаём твит
    tweet = Tweet(author_id=author_id, content=text)
    if media_objs:
        tweet.attachments = media_objs

    session.add(tweet)
    await session.flush()  # получили tweet.id

    # КОНСТРУИРУЕМ DTO БЕЗ ЛЕНИВОГО ДОСТУПА:
    # attachments берём из media_objs (они уже в памяти),
    # author берём из `author` (тоже в памяти),
    # likes пустой список.
    return TweetOut(
        id=tweet.id,
        content=tweet.content,
        attachments=[m.path for m in media_objs],
        author=_user_public(author),  # {id, name}
        likes=[],
    )


async def delete_tweet(session: AsyncSession, *, author_id: int, tweet_id: int) -> None:
    """
    Удалить твит (только свой).
    """
    tweet = (
        await session.execute(select(Tweet).where(Tweet.id == tweet_id).limit(1))
    ).scalar_one_or_none()
    if not tweet:
        raise EntityNotFound("tweet not found")

    if tweet.author_id != author_id:
        raise ForbiddenAction("cannot delete another user's tweet")

    await session.delete(tweet)


async def list_tweets(session: AsyncSession, *, author_id: int | None = None) -> List[TweetOut]:
    """
    Список твитов (опционально только автора).
    Формат строго по ТЗ: без created_at; author = {id, name}; likes = [{user_id, name}].
    """
    q = (
        select(Tweet)
        .options(
            selectinload(Tweet.author),  # автор
            selectinload(Tweet.attachments),  # медиа
        )
        .order_by(Tweet.created_at.desc())
    )
    if author_id is not None:
        q = q.where(Tweet.author_id == author_id)

    tweets = (await session.execute(q)).scalars().all()
    if not tweets:
        return []

    dtos: List[TweetOut] = []
    for t in tweets:
        likers = await _fetch_likers(session, t.id)
        dtos.append(_tweet_to_dto(t, likers=likers))
    return dtos


async def list_feed_for_user(session: AsyncSession, *, viewer_id: int) -> List[TweetOut]:
    """
    Лента: мои твиты + тех, на кого я подписан.
    Сортировка: по количеству лайков ↓, затем по дате ↓.
    """
    # авторы ленты
    followees_q = select(Follow.followee_id).where(Follow.follower_id == viewer_id)
    followee_ids = [row[0] for row in (await session.execute(followees_q)).all()]
    author_ids = followee_ids + [viewer_id] if followee_ids else [viewer_id]

    # агрегат лайков
    likes_agg = (
        select(Like.tweet_id, func.count(Like.id).label("likes_cnt"))
        .group_by(Like.tweet_id)
        .subquery()
    )

    # выборка твитов + сортировка
    q = (
        select(Tweet, func.coalesce(likes_agg.c.likes_cnt, 0).label("likes_cnt"))
        .where(Tweet.author_id.in_(author_ids))
        .outerjoin(likes_agg, likes_agg.c.tweet_id == Tweet.id)
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.attachments),
        )
        .order_by(
            func.coalesce(likes_agg.c.likes_cnt, 0).desc(),
            Tweet.created_at.desc(),
        )
    )

    rows = (await session.execute(q)).all()
    tweets = [row[0] for row in rows]
    if not tweets:
        return []

    # лайкнувшие + DTO
    dtos: List[TweetOut] = []
    for t in tweets:
        likers = await _fetch_likers(session, t.id)
        dtos.append(_tweet_to_dto(t, likers=likers))
    return dtos
