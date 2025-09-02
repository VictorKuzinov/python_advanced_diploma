from datetime import datetime
from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserPublic):
    followers: list[UserPublic] = []
    following: list[UserPublic] = []