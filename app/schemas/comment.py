"""
app/schemas/comment.py

Comment Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .user import UserResponse


# 基础模型 (共享字段)
class CommentBase(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


# 创建模型 (输入)
class CommentCreate(CommentBase):
    parent_id: UUID | None = Field(default=None, description="父评论ID，用于回复")

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "content": "这篇文章写得太好了，赞！",
                "parent_id": None,  # 顶级评论
            }
        },
    )


# 更新模型 (我们在此阶段不实现)
class CommentUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=1000)

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "content": "这篇文章写得太好了，赞！(编辑于 2025-10-08)",
            }
        },
    )


# 响应模型 (输出)
class CommentResponse(CommentBase):
    """
    返回给客户端的评论数据

    这个 Schema 需要展示一个层级结构，即一条评论可以包含一个回复列表，
    列表中的每个元素其自身也是一条评论。
    """

    id: UUID
    author: UserResponse  # 嵌套作者信息
    created_at: datetime
    replies: list["CommentResponse"] = []  # 递归模型：一个评论可以包含一组评论作为回复

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象创建
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "content": "This is a top-level comment.",
                "author": {
                    "id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
                    "username": "main_user",
                    "email": "main_user@example.com",
                    "created_at": "2025-10-08T10:00:00Z",
                },
                "created_at": "2025-10-08T11:00:00Z",
                "replies": [
                    {
                        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                        "content": "This is a reply to the comment.",
                        "author": {
                            "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                            "username": "reply_user",
                            "email": "reply_user@example.com",
                            "created_at": "2025-10-08T11:30:00Z",
                        },
                        "created_at": "2025-10-08T12:00:00Z",
                        "replies": [],
                    }
                ],
            }
        },
    )
