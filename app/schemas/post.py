from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.post import PostStatus
from app.schemas.common import PaginationParams

from .tag import TagResponse
from .user import UserSimpleResponse


# ============ 创建模型 ============
class PostCreate(BaseModel):
    """创建文章请求体

    特点：
    - tags: 允许客户端直接传递一个字符串列表，后端将处理"获取或创建"逻辑。
    - status: 创建文章status后端强制设置为draft。发布是一个单独的动作（可能触发通知、审核等）。
    - author_id： post创建模型不能包含 author_id 隐私字段

    用途：POST /api/v1/posts/
    """  # noqa: E501

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(
        default=None,
        max_length=200,
        description="URL标识默认按照标题自动生成",
    )
    tags: list[str] | None = Field(default=None, description="与文章关联的标签名称列表")

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API",
                "content": (
                    "FastAPI 是一个基于 Starlette 和 Pydantic 的现代、"
                    "高性能 Web 框架..."
                ),
                "tags": ["python", "fastapi", "webdev"],
            }
        },
    )


# ============ 更新模型 ============
class PostUpdate(BaseModel):
    """更新文章请求体

    特点：
    - 所有字段都是可选的，支持部分更新（PATCH）。
    - 不包含 `status` 字段，状态变更只能通过独立端点
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
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API (已更新)",
                "content": "在原文基础上，增加关于依赖注入的章节。",
                "tags": ["python", "fastapi", "di"],
            }
        },
    )


# ============ 响应模型 ============
class PostListResponse(BaseModel):
    """文章列表响应模型，不含正文内容

    用途：首页文章列表、搜索结果、标签下文章列表
    """

    id: UUID
    title: str
    slug: str
    summary: str | None = None
    status: PostStatus
    is_featured: bool = False
    published_at: datetime | None = None

    # 关联信息
    author: UserSimpleResponse
    tags: list[TagResponse] = []

    # 社交数据
    view_count: int = Field(default=0, description="文章浏览次数")
    like_count: int = Field(default=0, description="文章点赞数")
    favorite_count: int = Field(default=0, description="文章收藏数")

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(PostListResponse):
    """文章详情（含正文）

    用途：文章详情页、编辑页
    """

    content: str  # 唯一增加的字段
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象创建
        json_schema_extra={
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "title": "探索 FastAPI 的强大功能",
                    "status": "published",
                    "content": "FastAPI 是一个现代、快速的 Web 框架...",
                    "summary": "本文介绍了 FastAPI 的核心特性...",
                    "slug": "explore-fastapi-features",
                    "author": {
                        "id": "b1c2d3e4-f5a6-7890-1234-abcdef123456",
                        "username": "johndoe",
                        "nickname": "John D.",
                        "avatar": None,
                        "bio": None,
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


class PostLikeStatusResponse(BaseModel):
    """文章点赞状态响应"""

    post_id: UUID = Field(description="文章ID")
    is_liked: bool = Field(description="是否已点赞")
    like_count: int = Field(description="文章总点赞数")

    model_config = ConfigDict(from_attributes=True)


class PostFavoriteStatusResponse(BaseModel):
    """文章收藏状态响应"""

    post_id: UUID = Field(description="文章ID")
    is_favorited: bool = Field(description="是否已收藏")
    favorite_count: int = Field(description="文章总收藏数")

    model_config = ConfigDict(from_attributes=True)


# ============ 查询模型 ============
class PostQueryParams(BaseModel):
    """文章过滤请求参数

    用于文章列表查询时的过滤参数，支持多种过滤条件组合。

    特点：
    - 所有字段都是可选的，支持任意组合过滤
    - 使用 Field 提供清晰的描述和示例
    - 禁止额外字段，确保类型安全
    - ⚠️ 不支持 status 字段过滤，公开接口只返回已发布

    用途：GET /api/v1/posts/ 的查询参数
    """

    author_id: UUID | None = Field(
        default=None,
        description="按作者ID过滤文章",
        examples=["a1b2c3d4-e5f6-7890-1234-567890abcdef"],
    )
    tag_name: str | None = Field(
        default=None,
        description="按标签名称过滤文章",
        examples=["Python", "FastAPI", "Web开发"],
    )
    title_contains: str | None = Field(
        default=None,
        description="按标题关键词过滤文章（模糊匹配）",
        examples=["FastAPI", "教程", "入门"],
    )
    published_at_from: datetime | None = Field(
        default=None,
        description="按发布时间范围过滤（起始时间）",
        examples=["2024-01-01T00:00:00Z"],
    )
    published_at_to: datetime | None = Field(
        default=None,
        description="按发布时间范围过滤（结束时间）",
        examples=["2024-12-31T23:59:59Z"],
    )

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全，pydantic 默认是'ignore'
        json_schema_extra={
            "example": {
                "author_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "tag_name": "Python",
                "title_contains": "FastAPI",
                "published_at_from": "2024-06-01T00:00:00Z",
                "published_at_to": "2024-06-30T23:59:59Z",
            }
        },
    )


class PostPaginationParams(PaginationParams):
    """分页参数模型，修改排序默认字段为 published_at,支持置顶优先选项"""

    sort: str = Field(default="published_at", description="默认排序字段为published_at")
    prioritize_featured: bool = Field(default=True, description="默认优先显示置顶文章")

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "page": 1,
                "size": 20,
                "sort": "published_at",
                "order": "desc",
                "prioritize_featured": True,
            }
        },
    )
