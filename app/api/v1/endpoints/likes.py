from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.crud.post as post_crud
import app.crud.post_like as post_like_crud
from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.schemas.post import PostLikeStatusResponse
from app.schemas.user import UserResponse

# 注册点赞管理路由
router = APIRouter()


# ============================= 查询文章点赞用户列表 ===========================
@router.get("/{post_id}/liked-users", response_model=list[UserResponse])
async def get_post_liked_users(
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """查询文章点赞用户列表

    **权限：**
    - 公开访问，无需登录

    **路径参数**:
    - post_id: 文章的 UUID

    **查询参数**:
    - skip: 跳过的记录数（默认0）
    - limit: 返回的最大记录数（默认20）

    **返回**:
    - 文章点赞用户列表

    **示例**:
        GET /api/v1/posts/123e4567-e89b-12d3/liked-users?skip=0&limit=20
    """

    users = post_like_crud.get_post_liked_users(
        db=db, post_id=post_id, skip=skip, limit=limit
    )

    return users  # type: ignore


# ============================= 点赞操作 ===========================
@router.post("/{post_id}/likes", response_model=PostLikeStatusResponse)
async def toggle_like(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostLikeStatusResponse:
    """切换点赞状态（幂等）

    **使用场景**:
    - 用户点击点赞按钮，切换点赞状态，并触发通知
    - 用户点击取消点赞按钮，切换取消点赞


    **权限：**
    - 登录用户

    **路径参数**:
    - post_id: 帖子 ID

    **返回**:
    - 200: 切换成功
    - 404: 文章不存在
    - 403: 无权限点赞此文章

    **示例**:
        POST /api/v1/posts/123e4567-e89b-12d3/likes
    """

    # 1. 调用 CRUD 层切换点赞状态
    is_liked = post_like_crud.toggle_like(
        db=db, user_id=current_user.id, post_id=post_id
    )

    # 2. 获取更新后的文章信息
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    # 检查文章是否存在
    if post is None:
        raise ResourceNotFoundError(resource="文章")

    # 3. 返回响应
    return PostLikeStatusResponse(
        post_id=post_id, is_liked=is_liked, like_count=post.like_count
    )


# ============================= 查询当前用户对文章的点赞状态 ===========================
@router.get("/{post_id}/like-status", response_model=PostLikeStatusResponse)
async def get_like_status(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostLikeStatusResponse:
    """查询当前用户对文章的点赞状态

    **使用场景**:
    - 用户查看文章详情时，查询当前用户对文章的点赞状态

    **权限：**
    - 登录用户

    **路径参数**:
    - post_id: 文章的 UUID

    **返回**:
    - 200: 查询成功
    - 404: 文章不存在
    """

    # 1. 检查用户是否已点赞
    is_liked = post_like_crud.is_liked(db=db, user_id=current_user.id, post_id=post_id)

    # 2. 获取文章信息
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 3. 返回完整响应
    return PostLikeStatusResponse(
        post_id=post_id, is_liked=is_liked, like_count=post.like_count
    )
