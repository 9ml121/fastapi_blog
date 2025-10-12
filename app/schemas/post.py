"""
app/schemas/post.py

Post Pydantic Schemas - 文章数据验证与序列化

设计思路：
1. PostBase: 提取文章的核心业务字段，供其他 Schema 继承。
2. PostCreate: 创建文章时的输入数据，允许客户端提供标签名称列表。
3. PostUpdate: 更新文章时的输入数据，所有字段可选，支持部分更新。
4. PostResponse: 返回给客户端的数据，包含作者和标签的完整信息，并排除敏感数据。
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .tag import TagResponse
from .user import UserResponse


# ============ 基础模型 (共享字段) ============
class PostBase(BaseModel):
    """
    文章基础字段

    提取所有文章相关 Schema 都需要的核心业务字段。
    """

    title: str = Field(min_length=1, max_length=200, description="文章标题")
    content: str = Field(min_length=1, description="文章正文内容，支持 Markdown")
    summary: str | None = Field(
        default=None, max_length=500, description="文章摘要，用于列表页展示"
    )
    slug: str | None = Field(
        default=None,
        max_length=200,
        description="URL 友好标识，如果不提供则会根据标题自动生成",
    )


# ============ 创建模型 ============
class PostCreate(PostBase):
    """
    创建文章时的输入数据

    特点：
    - 继承 PostBase 的所有字段。
    - 允许客户端直接传递一个字符串列表作为标签，后端将处理“获取或创建”逻辑。
    - ⚠️ post创建模型不能包含 author_id 隐私字段

    用途：POST /api/v1/posts/
    """

    tags: list[str] | None = Field(default=None, description="与文章关联的标签名称列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API",
                "content": (
                    "FastAPI 是一个基于 Starlette 和 Pydantic 的现代、"
                    "高性能 Web 框架..."
                ),
                "summary": "本文将带你入门 FastAPI。",
                "slug": "how-to-build-api-with-fastapi",
                "tags": ["python", "fastapi", "webdev"],
            }
        }
    )


# ============ 更新模型 ============
class PostUpdate(BaseModel):
    """
    更新文章时使用的输入数据

    特点：
    - 所有字段都是可选的，支持部分更新（PATCH）。
    - 包含 `tags` 字段，允许全量更新文章的标签关联。

    用途：PATCH /api/v1/posts/{post_id}
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=200)
    tags: list[str] | None = Field(
        default=None, description="文章的全新标签列表，将覆盖旧的标签"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API (已更新)",
                "content": "在原文基础上，增加关于依赖注入的章节。",
                "tags": ["python", "fastapi", "di"],
            }
        }
    )


# ============ 响应模型 (从数据库读取) ============
class PostResponse(PostBase):
    """
    返回给客户端的文章数据

    特点：
    - 继承 PostBase 的核心字段。
    - 包含 `author` 和 `tags` 的完整嵌套信息，使用对应的 Response Schema。
    - 包含所有系统生成的和用于展示的状态字段。
    - ⚠️ 不包含任何未来可能添加的敏感字段。

    用途：所有返回单个或多个文章信息的 API 端点。
    """

    id: UUID = Field(description="文章唯一标识符")
    author: UserResponse = Field(description="文章作者的详细信息")
    tags: list[TagResponse] = Field(default=[], description="与文章关联的标签列表")
    created_at: datetime = Field(description="文章创建时间")
    updated_at: datetime = Field(description="文章最后更新时间")
    published_at: datetime | None = Field(
        default=None, description="文章发布时间，如果未发布则为 null"
    )
    view_count: int = Field(default=0, description="文章浏览次数")
    is_featured: bool = Field(default=False, description="是否为精选文章")

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象创建
        json_schema_extra={
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "title": "探索 FastAPI 的强大功能",
                    "content": "FastAPI 是一个现代、快速的 Web 框架...",
                    "summary": "本文介绍了 FastAPI 的核心特性...",
                    "slug": "explore-fastapi-features",
                    "author": {
                        "id": "b1c2d3e4-f5a6-7890-1234-abcdef123456",
                        "username": "johndoe",
                        "email": "johndoe@example.com",
                        "nickname": "John D.",
                        "is_active": True,
                        "role": "user",
                        "avatar": None,
                        "is_verified": True,
                        "last_login": "2025-10-09T12:00:00Z",
                        "created_at": "2025-01-01T10:00:00Z",
                        "updated_at": "2025-01-01T10:00:00Z",
                    },
                    "tags": [
                        {
                            "id": "c1d2e3f4-a5b6-7890-1234-fedcba987654",
                            "name": "Python",
                            "slug": "python",
                        }
                    ],
                    "created_at": "2025-10-09T10:00:00Z",
                    "updated_at": "2025-10-09T11:00:00Z",
                    "published_at": "2025-10-09T10:05:00Z",
                    "view_count": 1024,
                    "is_featured": False,
                }
            ]
        },
    )
