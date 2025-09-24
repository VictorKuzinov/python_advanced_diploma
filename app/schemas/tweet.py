from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserPublic


class LikeUser(BaseModel):
    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class TweetCreate(BaseModel):
    # тело запроса POST /api/tweets
    tweet_data: str = Field(..., min_length=1, max_length=280)
    tweet_media_ids: list[int] | None = None


class TweetOut(BaseModel):
    id: int
    content: str
    attachments: list[str]  # список относительных путей к медиа (как в ТЗ)
    author: UserPublic
    likes: list[LikeUser] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


# Обёртки под формат ответов ТЗ
class PostTweetResponse(BaseModel):
    result: bool = True
    tweet_id: int


class SimpleResult(BaseModel):
    result: bool = True


class TweetsResponse(BaseModel):
    result: bool = True
    tweets: list[TweetOut]
