from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    id: int
    name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserPublic):
    followers: list[UserPublic] = []
    following: list[UserPublic] = []