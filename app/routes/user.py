# app/routes/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.routes.dependencies import get_current_user
from app.schemas import SimpleResult, UserProfile, UserProfileResponse
from app.services import users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Текущий пользователь",
    description="Возвращает профиль текущего пользователя. Требует api-key.",
)
async def get_me(
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserProfileResponse:
    """Профиль текущего пользователя (`/api/users/me`)."""
    profile: UserProfile = await users.get_public_profile(session, _current_user.id)
    return UserProfileResponse(result=True, user=profile)


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Профиль пользователя",
    description="Возвращает публичный профиль пользователя по ID. Api-key не обязателен.",
)
async def get_user_profile(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> UserProfileResponse:
    """Публичный профиль пользователя (followers, following)."""
    profile: UserProfile = await users.get_public_profile(session, user_id)
    return UserProfileResponse(result=True, user=profile)


@router.post(
    "/{target_user_id}/follow",
    response_model=SimpleResult,
    summary="Подписаться на пользователя",
    description="Текущий пользователь подписывается на другого пользователя.",
)
async def follow_user(
    target_user_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SimpleResult:
    """Оформить подписку (follower → followee)."""
    await users.follow(session, follower_id=_current_user.id, followee_id=target_user_id)
    return SimpleResult(result=True)


@router.delete(
    "/{target_user_id}/follow",
    response_model=SimpleResult,
    summary="Отписаться от пользователя",
    description="Текущий пользователь отписывается от другого пользователя.",
)
async def unfollow_user(
    target_user_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SimpleResult:
    """Удалить подписку (follower → followee)."""
    await users.unfollow(session, follower_id=_current_user.id, followee_id=target_user_id)
    return SimpleResult(result=True)
