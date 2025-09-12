# app/routes/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.routes.dependencies import get_current_user  # централизованная проверка api-key
from app.schemas import SimpleResult, UserProfile, UserProfileResponse
from app.services import users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    _current_user: User = Depends(get_current_user),  # проверка api-key → 401
    session: AsyncSession = Depends(get_session),  # при неверном/отсутствующем
):
    profile: UserProfile = await users.get_public_profile(session, _current_user.id)
    return UserProfileResponse(result=True, user=profile)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    # здесь api-key не обязателен по ТЗ — это публичный профиль
    profile: UserProfile = await users.get_public_profile(session, user_id)
    return UserProfileResponse(result=True, user=profile)


@router.post("/{target_user_id}/follow", response_model=SimpleResult)
async def follow_user(
    target_user_id: int,
    _current_user: User = Depends(get_current_user),  # требует авторизации по api-key
    session: AsyncSession = Depends(get_session),
):
    await users.follow(session, follower_id=_current_user.id, followee_id=target_user_id)
    return SimpleResult(result=True)


@router.delete("/{target_user_id}/follow", response_model=SimpleResult)
async def unfollow_user(
    target_user_id: int,
    _current_user: User = Depends(get_current_user),  # требует авторизации по api-key
    session: AsyncSession = Depends(get_session),
):
    await users.unfollow(session, follower_id=_current_user.id, followee_id=target_user_id)
    return SimpleResult(result=True)
