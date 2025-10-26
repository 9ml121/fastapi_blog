"""
用户资料管理 API 端点

提供用户个人资料的查看、更新和密码修改功能。

设计要点：
1. 使用 /users/me 端点：安全、语义化，避免用户通过修改 URL 访问他人资料
2. PATCH vs PUT 语义区分：PATCH 用于部分更新（用户资料），PUT 用于完整替换（密码修改）
3. 职责分离：普通用户用 UserProfileUpdate，管理员用 UserUpdate
4. 安全验证：密码修改必须验证旧密码，防止会话劫持
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.crud import post_favorite as post_favorite_crud
from app.crud import post_like as post_like_crud
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.post import PostResponse
from app.schemas.user import PasswordChange, UserProfileUpdate, UserResponse, UserUpdate

# 创建路由器 - 前缀 /users 已在 main.py 中配置
router = APIRouter()


# ============================= 查询当前用户资料 ===========================
@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """获取当前用户资料

    **权限**: 需要登录且账户活跃

    **返回**:
    - 200: 当前用户的完整信息（排除敏感字段）

    **示例**:
        GET /api/v1/users/me
    """
    return current_user  # type: ignore


# ============================= 查询用户点赞文章列表 ===========================
@router.get("/me/liked-posts", response_model=list[PostResponse])
async def get_user_liked_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PostResponse]:
    """查询用户点赞文章列表

    **权限**: 需要登录
    **使用场景**: 查询用户点赞文章列表
    **示例**: GET /api/v1/users/me/liked-posts

    **返回**:
    - 200: 查询成功
    - 404: 用户不存在
    - 403: 无权限查询此用户点赞文章列表
    """
    posts = post_like_crud.get_user_liked_posts(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return posts  # type: ignore


# ============================= 查询用户收藏文章列表 ===========================
@router.get("/me/favorited-posts", response_model=list[PostResponse])
async def get_user_favorited_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PostResponse]:
    """查询用户收藏文章列表"""
    posts = post_favorite_crud.get_user_favorited_posts(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return posts  # type: ignore


# ============================= 更新当前用户资料 ===========================
@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
) -> User | None:
    """更新当前用户资料

    **权限**: 需要登录且账户活跃

    **请求体**:
    - UserProfileUpdate: 用户资料更新数据（所有字段可选）

    **返回**:
    - 200: 更新后的用户信息
    - 409: 新邮箱已被其他用户占用

    **示例**:
        PATCH /api/v1/users/me
        {
            "nickname": "新昵称",
            "email": "new@example.com"
        }
    """

    updated_user = user_crud.update_profile(
        db=db, user=current_user, profile_update=profile_update
    )
    return updated_user


# ============================= 修改当前用户密码 ===========================
@router.put("/me/password", response_model=dict[str, str])
def change_password(
    *,
    db: Session = Depends(get_db),
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """修改当前用户密码

    **权限**: 需要登录且账户活跃

    **请求体**:
    - PasswordChange: 密码修改请求（包含旧密码和新密码）

    **返回**:
    - 200: 密码修改成功
    - 400: 旧密码不正确
    - 422: 新密码不符合格式要求

    **示例**:
        PUT /api/v1/users/me/password
        {
            "old_password": "旧密码",
            "new_password": "新密码"
        }
    """
    user_crud.update_password(
        db=db,
        user=current_user,
        old_password=password_change.old_password,
        new_password=password_change.new_password,
    )

    return {"message": "密码修改成功"}


# ============================= 管理员更新用户信息 ===========================
@router.patch("/{user_id}", response_model=UserResponse, include_in_schema=False)
def update_user_by_admin(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),  # 管理员权限
) -> User | None:
    """管理员更新用户信息

    **权限**: 需要管理员权限,目前在Swagger UI隐藏该端点,只用于API调用

    **请求体**:
    - UserUpdate: 用户更新数据

    **返回**:
    """
    updated_user = user_crud.update_user(db=db, user_id=user_id, user_in=user_update)

    return updated_user
