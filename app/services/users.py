# app/services/users.py
# CRUD и бизнес-логика для пользователей
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AlreadyExists, EntityNotFound, ForbiddenAction
from app.models import Follow, User
from app.schemas import UserProfile, UserPublic


# ===== Внутренние хелперы (возвращают ORM) =====
async def _get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def _get_user_by_api_key(session: AsyncSession, api_key: str) -> Optional[User]:
    """Вернуть пользователя по API-ключу или None (для внутреннего использования)."""
    query_user = select(User).where(User.api_key == api_key).limit(1)
    result_user = await session.execute(query_user)
    return result_user.scalar_one_or_none()


async def list_followers(session: AsyncSession, user_id: int) -> list[User]:
    """Список подписчиков user_id (возвращает ORM-объекты)."""
    followers_query = (
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followee_id == user_id)
        .order_by(User.username.asc())
    )
    followers_result = await session.execute(followers_query)
    return list(followers_result.scalars().all())


async def list_following(session: AsyncSession, user_id: int) -> list[User]:
    """Список пользователей, на кого подписан user_id (возвращает ORM-объекты)."""
    following_query = (
        select(User)
        .join(Follow, Follow.followee_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(User.username.asc())
    )
    following_result = await session.execute(following_query)
    return list(following_result.scalars().all())


# ===== Публичные функции сервиса (контракты совпадают с роутами) =====
async def get_public_profile(session: AsyncSession, user_id: int) -> UserProfile:
    """Публичный профиль пользователя (для /api/users/{id})."""
    user = await _get_user_by_id(session, user_id)
    if not user:
        raise EntityNotFound("user not found")

    followers = await list_followers(session, user_id)
    following = await list_following(session, user_id)

    return UserProfile(
        id=user.id,
        username=user.username,
        followers=[UserPublic(id=u.id, username=u.username) for u in followers],
        following=[UserPublic(id=u.id, username=u.username) for u in following],
    )


async def follow(session: AsyncSession, *, follower_id: int, followee_id: int) -> None:
    """
    Оформить подписку follower_id -> followee_id. Запрещаем самоподписку
    и дубли (AlreadyExists).
    """
    if follower_id == followee_id:
        raise ForbiddenAction("cannot follow yourself")

    # оба пользователя должны существовать
    if not await _get_user_by_id(session, follower_id) or not await _get_user_by_id(
        session, followee_id
    ):
        raise EntityNotFound("user not found")

    async with session.begin_nested():  # SAVEPOINT
        session.add(Follow(follower_id=follower_id, followee_id=followee_id))
        try:
            await session.flush()  # нарушит UNIQUE -> IntegrityError
        except IntegrityError:
            raise AlreadyExists("subscription already exists")


async def unfollow(session: AsyncSession, *, follower_id: int, followee_id: int) -> None:
    """Отписка follower_id от followee_id. Идемпотентно: если записи нет — ок."""
    await session.execute(
        delete(Follow).where(
            Follow.follower_id == follower_id,
            Follow.followee_id == followee_id,
        )
    )
