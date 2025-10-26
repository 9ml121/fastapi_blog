"""
文章管理 API 端点

提供文章的创建、查询、更新、删除等功能

知识点：
1. RESTful 设计：使用标准 HTTP 方法表达操作语义
   （POST=创建, GET=查询, PATCH=更新, DELETE=删除）
2. 依赖注入链：db → current_user → current_active_user，每层只负责一个验证步骤
3. Response Model：FastAPI 自动将 ORM 对象转为 Pydantic Schema，过滤敏感字段

📋 FastAPI 参数顺序规则：
1.路径参数 (post_id: UUID) - 必须在前
2.请求体参数 (post_in: PostUpdate) - 在路径参数之后
3.查询参数 (params: PaginationParams) - 在请求体参数之后
4.依赖注入参数 (db: Session = Depends(...)) - 必须在最后
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

import app.crud.post as post_crud
from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import (
    ResourceNotFoundError,
)
from app.core.pagination import PaginatedResponse
from app.models.user import User
from app.schemas.post import (
    PostCreate,
    PostFilters,
    PostPaginationParams,
    PostResponse,
    PostUpdate,
)

# 创建路由器
router = APIRouter()


# ============================= 创建文章 ===========================
@router.post(path="/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """创建新文章，默认创建为草稿状态

    **权限**: 需要登录且账户活跃

    **请求体**:
    - PostCreate: 文章创建数据（标题、内容、标签等）

    **返回**:
    - 201: 文章创建成功
    - 400: 请求数据无效
    - 409: 文章 slug 已存在

    **示例**:
        POST /api/v1/posts/
        {
            "title": "FastAPI 入门教程",
            "content": "FastAPI 是一个现代、快速的 Web 框架...",
            "tags": ["Python", "FastAPI", "Web开发"]
        }
    """
    new_post = post_crud.create_post(db=db, post_in=post_in, author_id=current_user.id)
    return new_post  # type: ignore


# ============================= 查询已发布文章列表 ===========================
@router.get("/", response_model=PaginatedResponse[PostResponse])
async def get_published_posts(
    pagination_params: PostPaginationParams = Depends(),
    filters_params: PostFilters = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PostResponse]:
    """获取已发布文章列表（支持分页、排序、过滤）

    **权限**: 公开访问，无需登录

    **查询参数**:
    【分页参数】
        - page: 页码（从1开始，默认1）
        - size: 每页数量（1-100，默认20）
        - sort: 排序字段（⚠️默认优先显示置顶文章，然后是published_at）
        - order: 排序方向（asc/desc，默认desc）
        - prioritize_featured: 是否优先显示置顶文章（默认True）
    【过滤参数】
        - author_id: 按作者ID过滤（可选）
        - tag_name: 按标签名称过滤（可选）
        - title_contains: 按标题关键词过滤（可选）
        - published_at_from: 按发布时间范围过滤（起始时间，可选）
        - published_at_to: 按发布时间范围过滤（结束时间，可选）

    **返回**:
        - 200: 分页的文章列表
        - 422: 参数验证失败

    **示例**:
        - GET /api/v1/posts/?page=1&size=10&sort=created_at&order=desc
        - GET /api/v1/posts/?author_id=123
        - GET /api/v1/posts/?tag_name=Python&title_contains=FastAPI
        - GET /api/v1/posts/?published_at_from=2024-06-01T00:00:00Z
                &published_at_to=2024-06-30T23:59:59Z
        - GET /api/v1/posts/?published_at_from=2024-06-01T00:00:00Z
    """
    # 构建查询对象
    response = post_crud.get_published_posts_paginated(
        db, filters_params=filters_params, pagination_params=pagination_params
    )
    return response  # type: ignore

# ============================= 查询置顶文章列表 ===========================
@router.get("/featured", response_model=PaginatedResponse[PostResponse])
async def get_featured_posts(
    pagination_params: PostPaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PostResponse]:
    """获取置顶文章列表"""
    featured_posts = post_crud.get_featured_posts(
        db=db, pagination_params=pagination_params
    )

    return featured_posts  # type: ignore


# ============================= 查询用户草稿列表 ===========================
@router.get("/drafts", response_model=list[PostResponse])
async def get_user_drafts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PostResponse]:
    """查看用户草稿列表

    **权限**: 需要登录且是文章作者

    **返回**:
    - 200: 用户草稿列表
    - 403: 无权限查看草稿列表

    **示例**:
        GET /api/v1/posts/user/drafts
    """
    drafts = post_crud.get_user_drafts(db, user_id=current_user.id)
    return drafts  # type: ignore


# ============================= 查询单篇文章详情 ===========================
@router.get("/{post_id}", response_model=PostResponse)
async def get_post_detail(
    post_id: UUID,
    db: Session = Depends(get_db),
) -> PostResponse:
    """获取文章详情

    **权限**: 公开访问，无需登录

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 200: 文章详情
    - 404: 文章不存在

    **示例**:
        GET /api/v1/posts/123e4567-e89b-12d3-a456-426614174000
    """
    post = post_crud.get_post_by_id(db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")
    return post  # type: ignore




# ============================= 更新文章 ===========================
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """更新文章（部分更新）

    **权限**: 需要登录且是文章作者

    **路径参数**:
    - post_id: 文章的 UUID

    **请求体**:
    - PostUpdate: 文章更新数据（所有字段可选）

    **返回**:
    - 200: 更新后的文章详情
    - 404: 文章不存在
    - 403: 无权限修改此文章

    **示例**:
        PATCH /api/v1/posts/123e4567-e89b-12d3-a456-426614174000
        {
            "title": "更新后的标题",
            "tags": ["Python", "FastAPI"]
        }
    """

    updated_post = post_crud.update_post(
        db=db, post_id=post_id, user_id=current_user.id, post_in=post_in
    )

    return updated_post  # type: ignore


# ============================= 发布文章 ===========================
@router.patch("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """发布文章

    **权限**: 需要登录且是文章作者或admin

    **NOTE**:
    1. 管理员可以发布任何文章，作者只能发布自己的文章
    2. 只有草稿状态的文章才能发布,如果要重新发布已归档的，应该先转回草稿

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 200: 发布成功
    - 404: 文章不存在
    - 403: 无权限发布此文章
    - 409: 文章状态不正确，只有草稿状态才能发布

    **示例**:
        PATCH /api/v1/posts/123e4567-e89b-12d3-a456-426614174000/publish

    """
    published_post = post_crud.publish_post(
        db=db, post_id=post_id, user_id=current_user.id
    )
    return published_post  # type: ignore


# ============================= 归档文章 ===========================
@router.patch("/{post_id}/archive", response_model=PostResponse)
async def archive_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """归档文章

    **权限**: 需要登录且是文章作者或admin

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 200: 归档成功
    - 404: 文章不存在
    - 403: 无权限归档此文章
    - 409: 文章状态不正确，只有已发布状态才能归档

    **示例**:
        PATCH /api/v1/posts/123e4567-e89b-12d3-a456-426614174000/archive
    """
    archived_post = post_crud.archive_post(
        db=db, post_id=post_id, user_id=current_user.id
    )

    return archived_post  # type: ignore


# ============================= 回退文章为草稿状态 ===========================
@router.patch("/{post_id}/revert-to-draft", response_model=PostResponse)
async def revert_to_draft(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """回退文章为草稿状态

    **权限**: 需要登录且是文章作者或 admin

    **使用场景**:
    - 已发布文章需要修改：回退为草稿 → 编辑 → 重新发布
    - 已归档文章需要重新处理：回退为草稿 → 编辑或发布

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 200: 回退成功
    - 404: 文章不存在
    - 403: 无权限回退此文章
    - 409: 文章已是草稿状态
    """

    reverted_post = post_crud.revert_post_to_draft(
        db=db, post_id=post_id, user_id=current_user.id
    )
    return reverted_post  # type: ignore


# ============================= 切换文章置顶状态 ===========================
@router.patch("/{post_id}/toggle-featured", response_model=PostResponse)
async def toggle_post_featured(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostResponse:
    """切换文章置顶状态（仅管理员）

      **权限**: 需要管理员权限

      **使用场景**: 切换文章的置顶状态（置顶/取消置顶）

      **路径参数**:
      - post_id: 文章的 UUID

      **返回**:
      - 200: 切换成功
      - 404: 文章不存在
      - 403: 无权限切换此文章

      **示例**: PATCH /api/v1/posts/123e4567-e89b-12d3-a456-426614174000/toggle-featured

    """
    featured_post = post_crud.toggle_post_featured(
        db=db, post_id=post_id, user_id=current_user.id
    )
    return featured_post  # type: ignore


# ============================= 删除文章 ===========================
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """删除文章

    **权限**: 需要登录且是文章作者或admin

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 204: 删除成功（无响应体）
    - 404: 文章不存在
    - 403: 无权限删除此文章

    **示例**:
        DELETE /api/v1/posts/123e4567-e89b-12d3-a456-426614174000
    """
    post_crud.delete_post(db=db, post_id=post_id, user_id=current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
