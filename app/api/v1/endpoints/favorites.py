from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.crud.post as post_crud
import app.crud.post_favorite as post_favorite_crud
from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.schemas.post import PostFavoriteStatusResponse
from app.schemas.user import UserResponse

# 注册收藏管理路由
router = APIRouter()


# ============================= 收藏操作 ===========================
@router.post("/{post_id}/favorites", response_model=PostFavoriteStatusResponse)
async def toggle_favorite(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostFavoriteStatusResponse:
    """切换收藏状态（幂等）"""

    # 1. 调用 CRUD 层切换收藏状态
    is_favorited = post_favorite_crud.toggle_favorite(
        db=db, user_id=current_user.id, post_id=post_id
    )

    # 2. 获取更新后的文章信息
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    # 检查文章是否存在
    if post is None:
        raise ResourceNotFoundError(resource="文章")

    # 3. 返回响应
    return PostFavoriteStatusResponse(
        post_id=post_id, is_favorited=is_favorited, favorite_count=post.favorite_count
    )


# ============================= 查询当前用户对文章的收藏状态 ===========================
@router.get("/{post_id}/favorite-status", response_model=PostFavoriteStatusResponse)
async def get_favorite_status(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostFavoriteStatusResponse:
    """查询当前用户对文章的收藏状态"""

    # 1. 检查用户是否已收藏
    is_favorited = post_favorite_crud.is_favorited(
        db=db, user_id=current_user.id, post_id=post_id
    )

    # 2. 获取文章信息
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 3. 返回响应
    return PostFavoriteStatusResponse(
        post_id=post_id, is_favorited=is_favorited, favorite_count=post.favorite_count
    )


# ============================= 查询文章收藏用户列表 ===========================
@router.get("/{post_id}/favorited-users", response_model=list[UserResponse])
async def get_post_favorited_users(
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """查询文章收藏用户列表"""
    users = post_favorite_crud.get_post_favorited_users(
        db=db, post_id=post_id, skip=skip, limit=limit
    )
    return users  # type: ignore
