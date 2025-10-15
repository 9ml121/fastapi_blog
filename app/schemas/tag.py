"""
app/schemas/tag.py

Tag Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# 基础模型 (共享字段)
class TagBase(BaseModel):
    name: str
    description: str | None = None


# 创建模型
class TagCreate(TagBase):
    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "name": "Python",
                "description": "关于 Python 编程语言的所有文章。",
            }
        },
    )


# 更新模型
class TagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "description": "关于 Python 3.8+ 编程语言的所有文章。",
            }
        },
    )


# 响应模型 (从数据库读取)
class TagResponse(TagBase):
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    post_count: int

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象创建
        json_schema_extra={
            "example": {
                "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "name": "Python",
                "description": "关于 Python 编程语言的所有文章。",
                "slug": "python",
                "created_at": "2024-10-01T10:00:00Z",
                "updated_at": "2024-10-01T10:00:00Z",
                "post_count": 42,
            }
        },
    )


# ============================================
# 标签详情模型（包含文章列表，避免循环引用）
# ============================================


class PostInTag(BaseModel):
    """标签详情中的简化文章信息（避免与 PostResponse 循环引用）"""

    id: UUID
    title: str
    summary: str | None
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagWithPosts(TagResponse):
    """标签详情响应（包含关联文章列表）

    用于 GET /tags/{slug} 端点，返回标签信息及其关联的所有文章。
    为避免循环引用，文章信息使用简化版 PostInTag。
    """

    posts: list[PostInTag] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "name": "Python",
                "description": "关于 Python 编程语言的所有文章。",
                "slug": "python",
                "created_at": "2024-10-01T10:00:00Z",
                "updated_at": "2024-10-01T10:00:00Z",
                "post_count": 5,
                "posts": [
                    {
                        "id": "b1c2d3e4-f5a6-7890-1234-abcdef123456",
                        "title": "FastAPI 入门教程",
                        "summary": "从零开始学习 FastAPI",
                        "slug": "fastapi-tutorial",
                        "created_at": "2024-10-01T10:00:00Z",
                    }
                ],
            }
        },
    )
