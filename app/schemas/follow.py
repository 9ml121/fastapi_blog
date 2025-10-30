from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# 关注状态响应
class FollowResponse(BaseModel):
    follower_id: UUID = Field(description="关注者ID")
    followed_id: UUID = Field(description="被关注者ID")
    created_at: datetime = Field(description="关注时间")

    model_config = ConfigDict(from_attributes=True)


# 用户简化响应（用于关注/粉丝列表）
class FollowUserSummary(BaseModel):
    id: UUID = Field(description="用户ID")
    username: str = Field(description="用户名")

    nickname: str | None = Field(default=None, description="昵称")
    avatar: str | None = Field(default=None, description="头像URL")
    bio: str | None = Field(default=None, description="个人签名")
    is_following: bool = Field(description="当前登录用户是否已关注")

    model_config = ConfigDict(from_attributes=True)
