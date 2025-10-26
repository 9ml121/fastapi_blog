"""
app/schemas/post.py

Post Pydantic Schemas - 文章数据验证与序列化

设计思路：
1. PostBase: 提取文章的核心业务字段，供其他 Schema 继承。
2. PostCreate: 创建文章时的输入数据，允许客户端提供标签名称列表。
3. PostUpdate: 更新文章时的输入数据，所有字段可选，支持部分更新。
4. PostResponse: 返回给客户端的数据，包含作者和标签的完整信息，并排除敏感数据。
5. PostFilters: 文章过滤条件，支持多种过滤条件组合。
6. PostPaginationParams：继承 PaginationParams，修改排序默认字段为 published_at。
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginationParams
from app.models.post import PostStatus

from .tag import TagResponse
from .user import UserResponse


# ============ 基础模型 (共享字段) ============
class PostBase(BaseModel):
    """文章基础字段

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
    """创建文章时的输入数据

    特点：
    - 继承 PostBase 的所有字段。
    - 允许客户端直接传递一个字符串列表作为标签，后端将处理"获取或创建"逻辑。
    - status 字段允许指定初始状态，默认为 draft（草稿）
    - ⚠️ post创建模型不能包含 author_id 隐私字段

    用途：POST /api/v1/posts/
    """

    status: PostStatus = Field(
        default=PostStatus.DRAFT, description="文章初始状态（draft/published/archived）"
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
                "summary": "本文将带你入门 FastAPI。",
                "slug": "how-to-build-api-with-fastapi",
                "status": "draft",
                "tags": ["python", "fastapi", "webdev"],
            }
        },
    )


# ============ 更新模型 ============
class PostUpdate(BaseModel):
    """
    更新文章时使用的输入数据

    特点：
    - 所有字段都是可选的，支持部分更新（PATCH）。
    - 包含 `status` 字段，允许更改文章状态（发布、撤回、归档）
    - 包含 `tags` 字段，允许全量更新文章的标签关联。

    用途：PATCH /api/v1/posts/{post_id}
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=200)
    status: PostStatus | None = Field(
        default=None, description="文章状态（draft/published/archived）"
    )
    tags: list[str] | None = Field(
        default=None, description="文章的全新标签列表，将覆盖旧的标签"
    )

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API (已更新)",
                "content": "在原文基础上，增加关于依赖注入的章节。",
                "status": "published",
                "tags": ["python", "fastapi", "di"],
            }
        },
    )


# ============ 响应模型 (从数据库读取) ============
# TODO: 待增加 ListPostResponse 模型，用于返回多个文章的列表数据
class PostResponse(PostBase):
    """返回给客户端的文章数据

    特点：
    - 继承 PostBase 的核心字段。
    - 包含 `author` 和 `tags` 的完整嵌套信息，使用对应的 Response Schema。
    - 包含所有系统生成的和用于展示的状态字段。
    - ⚠️ 包含 `status` 字段，用于前端判断文章可见性


    用途：所有返回单个或多个文章信息的 API 端点。
    """

    id: UUID = Field(description="文章唯一标识符")
    author: UserResponse = Field(description="文章作者的详细信息")
    tags: list[TagResponse] = Field(default=[], description="与文章关联的标签列表")
    status: PostStatus = Field(description="文章状态（draft/published/archived）")
    created_at: datetime = Field(description="文章创建时间")
    updated_at: datetime = Field(description="文章最后更新时间")
    published_at: datetime | None = Field(
        default=None, description="文章发布时间，如果未发布则为 null"
    )
    is_featured: bool = Field(default=False, description="是否为精选文章")

    # 社交互动数据
    view_count: int = Field(default=0, description="文章浏览次数")
    like_count: int = Field(default=0, description="文章点赞数")
    favorite_count: int = Field(default=0, description="文章收藏数")


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

# ============ post过滤模型 ============
class PostFilters(BaseModel):
    """文章过滤条件

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


# ============ 分页参数模型 ============
class PostPaginationParams(PaginationParams):
    """分页参数模型，修改排序默认字段为 published_at,支持置顶优先选项
    """

    sort: str = Field(
        default="published_at", description="排序字段（默认published_at）"
    )

    prioritize_featured: bool = Field(default=True, description="是否优先显示置顶文章")

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
