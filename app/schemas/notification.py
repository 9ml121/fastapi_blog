from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationType
from app.schemas.post import PostSimpleResponse
from app.schemas.user import UserSimpleResponse


# 通知响应模型（含聚合）
class NotificationResponse(BaseModel):
    id: UUID = Field(description="通知ID")
    actor: UserSimpleResponse = Field(description="操作发起人")
    notification_type: NotificationType = Field(description="通知类型")
    aggregated_count: int = Field(description="聚合操作数")

    post: PostSimpleResponse | None = Field(description="关联的文章（如有）")
    is_read: bool = Field(description="是否已读")
    created_at: datetime = Field(description="创建时间")
    read_at: datetime | None = Field(description="标记已读的时间")

    message: str = Field(description="通知文案，支持聚合显示")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "actor": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "用户 A",
                        "nickname": "用户 A",
                        "avatar": "https://example.com/avatar.png",
                        "bio": "个人简介",
                    },
                    "notification_type": "like",
                    "message": "用户 A 赞了你的文章《标题》",
                    "aggregated_count": 1,
                    "post": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "标题",
                        "slug": "slug",
                        "author": "550e8400-e29b-41d4-a716-446655440000",
                    },
                    "is_read": False,
                    "created_at": "2025-01-01T00:00:00Z",
                    "read_at": None,
                }
            ]
        },
    )
