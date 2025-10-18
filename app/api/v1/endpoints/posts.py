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
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.pagination import PaginatedResponse, PaginationParams
from app.core.exceptions import (
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.crud.post import post as post_crud
from app.models.user import User
from app.schemas.post import PostCreate, PostFilters, PostResponse, PostUpdate

# 创建路由器
router = APIRouter()


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
    new_post = post_crud.create_with_author(
        db=db,
        obj_in=post_in,
        author_id=current_user.id,
    )
    return new_post  # type: ignore


@router.get("/", response_model=PaginatedResponse[PostResponse])
async def get_posts(
    params: PaginationParams = Depends(),
    filters: PostFilters = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PostResponse]:
    """获取文章列表（支持分页、排序、过滤）

    **权限**: 公开访问，无需登录

    **查询参数**:
    - page: 页码（从1开始，默认1）
    - size: 每页数量（1-100，默认20）
    - sort: 排序字段（默认created_at）
    - order: 排序方向（asc/desc，默认desc）
    - author_id: 按作者ID过滤（可选）
    - tag_name: 按标签名称过滤（可选）
    - is_published: 按发布状态过滤（可选）
    - title_contains: 按标题关键词过滤（可选）
    - published_at_from: 按发布时间范围过滤（起始时间，可选）
    - published_at_to: 按发布时间范围过滤（结束时间，可选）

    **返回**:
    - 200: 分页的文章列表
    - 422: 参数验证失败

    **示例**:
    - GET /api/v1/posts/?page=1&size=10&sort=created_at&order=desc
    - GET /api/v1/posts/?author_id=123&is_published=true
    - GET /api/v1/posts/?tag_name=Python&title_contains=FastAPI
    - GET /api/v1/posts/?published_at_from=2024-06-01T00:00:00Z
            &published_at_to=2024-06-30T23:59:59Z
    - GET /api/v1/posts/?published_at_from=2024-06-01T00:00:00Z
            &is_published=true
    """
    # 调用 CRUD 方法获取分页数据
    posts, total = post_crud.get_paginated(db, params=params, filters=filters)

    # 构建分页响应
    return PaginatedResponse.create(posts, total, params)  # type: ignore


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


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
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
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    return post  # type: ignore


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
    # 1. 获取文章
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 检查权限：只有作者可以更新
    if post.author_id != current_user.id:
        raise PermissionDeniedError(message="无权限修改此文章")

    # 3. 执行更新
    updated_post = post_crud.update(db=db, db_obj=post, obj_in=post_in)

    return updated_post  # type: ignore


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除文章

    **权限**: 需要登录且是文章作者

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 204: 删除成功（无响应体）
    - 404: 文章不存在
    - 403: 无权限删除此文章

    **示例**:
        DELETE /api/v1/posts/123e4567-e89b-12d3-a456-426614174000
    """
    # 1. 获取文章并检查存在性
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 检查权限：只有作者可以删除
    if post.author_id != current_user.id:
        raise PermissionDeniedError(message="无权限删除此文章")

    # 3. 执行删除
    post_crud.remove(db, id=post_id)

    # FastAPI 自动返回 204
    return None


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
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 检查权限：作者或管理员
    if post.author_id != current_user.id and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限发布此文章")

    # 执行发布
    published_post = post_crud.publish(db, post_id=post_id)

    return published_post  # type: ignore


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
    # 1. 检查文章是否存在和权限
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 检查权限：作者或管理员
    if post.author_id != current_user.id and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限归档此文章")

    # 3. 执行归档
    archived_post = post_crud.archive(db, post_id=post_id)

    return archived_post  # type: ignore


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
    # 1. 检查文章是否存在和权限
    post = post_crud.get(db, id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    if post.author_id != current_user.id and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限回退此文章")

    # 2. 执行回退操作（业务规则校验在 CRUD 层）
    reverted_post = post_crud.revert_to_draft(db, post_id=post_id)
    return reverted_post  # type: ignore
