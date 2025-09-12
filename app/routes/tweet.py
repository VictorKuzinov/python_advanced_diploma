# app/routes/tweet.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.routes.dependencies import get_current_user
from app.schemas import PostTweetResponse, SimpleResult, TweetCreate, TweetsResponse
from app.services import likes as like_service
from app.services import tweets as tweet_service

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


@router.post("", response_model=PostTweetResponse)
async def create_tweet(
    payload: TweetCreate,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    dto = await tweet_service.create_tweet(
        session,
        author_id=_current_user.id,
        content=payload.tweet_data,
        media_ids=payload.tweet_media_ids or [],
    )
    return PostTweetResponse(result=True, tweet_id=dto.id)


@router.get("", response_model=TweetsResponse)
async def list_feed(
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    items = await tweet_service.list_feed_for_user(session, viewer_id=_current_user.id)
    return TweetsResponse(result=True, tweets=items)


@router.delete("/{tweet_id}", response_model=SimpleResult)
async def delete_tweet(
    tweet_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await tweet_service.delete_tweet(session, author_id=_current_user.id, tweet_id=tweet_id)
    return SimpleResult(result=True)


@router.post("/{tweet_id}/likes", response_model=SimpleResult)
async def like_tweet(
    tweet_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await like_service.like_tweet(session, user_id=_current_user.id, tweet_id=tweet_id)
    return SimpleResult(result=True)


@router.delete("/{tweet_id}/likes", response_model=SimpleResult)
async def unlike_tweet(
    tweet_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await like_service.unlike_tweet(session, user_id=_current_user.id, tweet_id=tweet_id)
    return SimpleResult(result=True)
