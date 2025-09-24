# app/schemas/user.py
from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    id: int
    name: str = Field(alias="username", serialization_alias="name")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserProfile(UserPublic):
    followers: list[UserPublic]
    following: list[UserPublic]
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    result: bool = True
    user: UserProfile


class UserWithFollowing(BaseModel):
    id: int
    name: str = Field(alias="username", serialization_alias="name")
    following: list[UserPublic]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
