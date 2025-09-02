# app/services/users.py
# CRUD и бизнес логика для пользователей
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import User, Follow
from app.schemas import UserPublic, UserProfile
from app.exceptions import AlreadyExists, EntityNotFound, ForbiddenAction


async def get_user_by_api_key(session: AsyncSession, api_key: str) -> Optional[User]:
    """Вернуть пользователя по API-ключу или None."""
    stmt = select(User).where(User.api_key == api_key).limit(1)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Вернуть пользователя по ID или None."""
    stmt = select(User).where(User.id == user_id).limit(1)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_public_profile(session: AsyncSession, user_id: int) -> UserProfile:
    """Возвращает публичный профиль
    {id, name, followers[], following[]}
    или выбрасывает EntityNotFound."""

    # сам пользователь
    user = (await session.execute(
        select(User).where(User.id == user_id).limit(1)
    )).scalar_one_or_none()

    if not user:
        raise EntityNotFound("User not found")

    # подписчики (кто подписан на user_id)
    followers = (await session.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followee_id == user_id)
    )).scalars().all()

    # на кого подписан user_id
    following = (await session.execute(
        select(User)
        .join(Follow, Follow.followee_id == User.id)
        .where(Follow.follower_id == user_id)
    )).scalars().all()

    # собираем DTO
    return UserProfile(
        **UserPublic.model_validate(user).model_dump(),
        followers=[UserPublic.model_validate(u) for u in followers],
        following=[UserPublic.model_validate(u) for u in following],
    )


async def follow(
    session: AsyncSession, *, follower_id: int, followee_id: int
) -> None:
    """Оформить подписку follower_id -> followee_id.
    Запрещаем самоподписку. Проверяем, что оба пользователя существуют.
    Дубликат подписки превращаем в AlreadyExists.
    """
    if follower_id == followee_id:
        raise ForbiddenAction("cannot follow yourself")

    # убеждаемся, что оба пользователя существуют
    follower = (await session.execute(
        select(User).where(User.id == follower_id).limit(1)
    )).scalar_one_or_none()
    followee = (await session.execute(
        select(User).where(User.id == followee_id).limit(1)
    )).scalar_one_or_none()

    if not follower or not followee:
        raise EntityNotFound("user not found")

    # создаём запись подписки
    session.add(Follow(follower_id=follower_id, followee_id=followee_id))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        # нарушена уникальная пара (follower_id, followee_id)
        raise AlreadyExists("subscription already exists")


async def unfollow(
    session: AsyncSession, *, follower_id: int, followee_id: int
) -> None:
    """Отписка follower_id от followee_id. Идемпотентно: если записи нет — ок."""
    await session.execute(
        delete(Follow).where(
            Follow.follower_id == follower_id, Follow.followee_id == followee_id
        )
    )
    await session.commit()


async def list_followers(session: AsyncSession, user_id: int) -> list[User]:
    """Список пользователей, которые подписаны на user_id."""
    stmt = (
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followee_id == user_id)
        .order_by(User.username.asc())
    )
    lst_followers =  await session.execute(stmt)
    return list(lst_followers.scalars().all())


async def list_following(session: AsyncSession, user_id: int) -> list[User]:
    """Список пользователей, на кого подписан user_id."""
    stmt = (
        select(User)
        .join(Follow, Follow.followee_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(User.username.asc())
    )
    lst_following = await session.execute(stmt)
    return list(lst_following.scalars().all())
