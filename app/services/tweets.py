# app/services/tweets.py
# CRUD и бизнес-логика для пользователей
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import DomainValidation, EntityNotFound, ForbiddenAction
from app.models import Media, Tweet, User, Like
from app.schemas import UserPublic, TweetOut, LikeUser


def _tweet_to_dto(tweet: Tweet, *, likers: list[User] | None = None) -> TweetOut:
    return TweetOut(
        id=tweet.id,
        content=tweet.content,
        created_at=tweet.created_at,
        attachments=[m.path for m in tweet.attachments],
        author=UserPublic.model_validate(tweet.author),
        likes=[LikeUser(user_id=u.id, name=u.username) for u in (likers or [])],
    )


async def create_tweet(
    session: AsyncSession,
    *,
    author_id: int,
    content: str,
    media_ids: list[int] | None = None,
) -> TweetOut:
    """Создать новый твит с опциональными медиа."""

    # Проверка текста
    text = (content or "").strip()
    if not text:
        raise DomainValidation("tweet content cannot be empty")
    if len(text) > 280:
        raise DomainValidation("tweet content must be ≤ 280 characters")

    # Проверка автора
    author = (
        await session.execute(select(User).where(User.id == author_id).limit(1))
    ).scalar_one_or_none()
    if not author:
        raise EntityNotFound("author not found")

    # Проверка медиа
    media_objs = []
    if media_ids:
        media_q = select(Media).where(Media.id.in_(media_ids))
        media_objs = (await session.execute(media_q)).scalars().all()
        if len(media_objs) != len(set(media_ids)):
            raise EntityNotFound("one or more media not found")

    # Создание твита
    tweet = Tweet(author_id=author_id, content=text)
    if media_objs:
        tweet.attachments = list(media_objs)

    session.add(tweet)
    await session.commit()
    await session.refresh(tweet)

    return _tweet_to_dto(tweet, likers=[])


async def delete_tweet(
    session: AsyncSession, *, author_id: int, tweet_id: int
) -> None:
    """
    Удалить твит (только свой).

    Raises:
        EntityNotFound: твит не найден
        ForbiddenAction: попытка удалить чужой твит
    """
    tweet = (
        await session.execute(
            select(Tweet).where(Tweet.id == tweet_id).limit(1)
        )
    ).scalar_one_or_none()
    if not tweet:
        raise EntityNotFound("tweet not found")

    if tweet.author_id != author_id:
        raise ForbiddenAction("cannot delete another user's tweet")

    await session.delete(tweet)
    await session.commit()


async def list_tweets(session, *, author_id: int | None = None) -> list[TweetOut]:
    query = (
        select(Tweet)
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.attachments),
        )
        .order_by(Tweet.created_at.desc())
    )
    if author_id is not None:
        query = query.where(Tweet.author_id == author_id)

    tweets = (await session.execute(query)).scalars().all()

    # вытащим лайкнувших для каждого твита (просто и понятно, без оптимизаций)
    dtos: list[TweetOut] = []
    for t in tweets:
        likers_q = (
            select(User)
            .join(Like, Like.user_id == User.id)
            .where(Like.tweet_id == t.id)
            .order_by(User.username.asc())
        )
        likers = (await session.execute(likers_q)).scalars().all()
        dtos.append(_tweet_to_dto(t, likers=likers))

    return dtos