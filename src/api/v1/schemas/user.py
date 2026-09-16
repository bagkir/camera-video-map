from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.api.v1.schemas.video import VideoListItem


class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=72)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str


class UserDashboard(BaseModel):
    user: UserOut
    recent_videos: list[VideoListItem]
