"""
# -   `POST /users/{user_id}/follow` - 关注用户
# -   `DELETE /users/{user_id}/follow` - 取消关注
# -   `GET /users/{user_id}/followers` - 获取粉丝列表
# -   `GET /users/{user_id}/following` - 获取关注列表
# -   `GET /users/{user_id}/follower-count` - 获取粉丝数
# -   `GET /users/me/is-following/{user_id}` - 检查是否已关注
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user_optional, get_db
from app.crud import follow as follow_crud
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.follow import FollowResponse, FollowUserSummary

router = APIRouter()


# ============================= 关注用户 ===========================
@router.post(
    "/{user_id}/follow",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def follow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FollowResponse:
    """关注用户

    **权限**: 需要登录

    **路径参数**:
    - user_id: 被关注用户的 UUID

    **返回**:
    - FollowResponse: 关注关系

    **示例**:
    POST /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/follow
    """

    return follow_crud.follow_user(
        db=db, follower_id=current_user.id, followed_id=user_id
    )  # type: ignore


# ============================= 取消关注 ===========================
@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """取消关注用户

    **权限**: 需要登录

    **路径参数**:
    - user_id: 被取消关注用户的 UUID

    **返回**:
    - 204: 取消关注成功（无响应体）
    - 404: 关注关系不存在

    **示例**:
    DELETE /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/follow
    """
    follow_crud.unfollow_user(db=db, follower_id=current_user.id, followed_id=user_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================= 获取粉丝列表 ===========================
@router.get("/{user_id}/followers", response_model=PaginatedResponse[FollowUserSummary])
async def get_followers(
    user_id: UUID,
    pagination_params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_current_user_optional),
) -> PaginatedResponse[FollowUserSummary]:
    """获取当前用户的粉丝列表

    **权限**: 公开访问，无需登录

    **路径参数**:
    - user_id: 被获取粉丝用户的 UUID

    **查询参数**:
    - pagination_params: 分页参数

    **返回**:
    - PaginatedResponse[FollowUserSummary]: 粉丝列表

    **示例**:
    GET /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/followers
    """
    items, total = follow_crud.get_followers(
        db=db,
        user_id=user_id,
        pagination_params=pagination_params,
        viewer_id=viewer.id if viewer else None,
    )

    return PaginatedResponse.create(
        schema_class=FollowUserSummary,
        items=items,
        total=total,
        params=pagination_params,
    )


# ============================= 获取关注列表 ===========================
@router.get("/{user_id}/following", response_model=PaginatedResponse[FollowUserSummary])
async def get_following(
    user_id: UUID,
    pagination_params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_current_user_optional),
) -> PaginatedResponse[FollowUserSummary]:
    """获取当前用户的关注列表

    **权限**: 公开访问，无需登录

    **路径参数**:
    - user_id: 被获取关注用户的 UUID

    **查询参数**:
    - pagination_params: 分页参数

    **返回**:
    - PaginatedResponse[FollowUserSummary]: 关注列表

    **示例**:
    GET /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/following
    """
    items, total = follow_crud.get_following(
        db=db,
        user_id=user_id,
        pagination_params=pagination_params,
        viewer_id=viewer.id if viewer else None,
    )

    return PaginatedResponse.create(
        items=items,
        total=total,
        params=pagination_params,
        schema_class=FollowUserSummary,
    )


# ============================= 获取粉丝数 ===========================
@router.get("/{user_id}/follower-count")
async def get_follower_count(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> int:
    """获取当前用户的粉丝数

    **权限**: 公开访问，无需登录

    **路径参数**:
    - user_id: 被获取粉丝数的用户的 UUID

    **返回**:
    - int: 粉丝数

    **示例**:
    GET /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/follower-count
    """
    return follow_crud.get_follower_count(db=db, user_id=user_id)


# ============================= 检查是否已关注 ===========================
@router.get("/me/is-following/{user_id}")
async def is_following(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> bool:
    """检查当前用户是否已关注目标用户

    **权限**: 需要登录

    **路径参数**:
    - user_id: 被检查是否已关注的用户的 UUID

    **返回**:
    - bool: 是否已关注

    **示例**:
    GET /api/v1/follows/123e4567-e89b-12d3-a456-426614174000/is-following
    """
    return follow_crud.is_following(
        db=db, follower_id=current_user.id, followed_id=user_id
    )
