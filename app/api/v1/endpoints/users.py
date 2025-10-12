"""
用户资料管理 API 端点

提供用户个人资料的查看、更新和密码修改功能。

设计要点：
1. 使用 /users/me 端点：安全、语义化，避免用户通过修改 URL 访问他人资料
2. PATCH vs PUT 语义区分：PATCH 用于部分更新（用户资料），PUT 用于完整替换（密码修改）
3. 职责分离：普通用户用 UserProfileUpdate，管理员用 UserUpdate（Phase 6 实现）
4. 安全验证：密码修改必须验证旧密码，防止会话劫持
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import PasswordChange, UserProfileUpdate, UserResponse

# 创建路由器 - 前缀 /users 已在 main.py 中配置
router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取当前用户资料

    设计亮点：
    - 极简实现：依赖注入已提供 current_user，直接返回即可
    - response_model=UserResponse 自动过滤敏感字段（如 password_hash）
    - 使用 /me 端点避免用户 ID 泄露和权限越界

    Returns:
        当前用户的完整信息（排除敏感字段）

    """
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新当前用户资料

    业务逻辑：
    1. 验证用户已登录（JWT Token）
    2. 如果更新邮箱，检查新邮箱是否已存在（排除自己）
    3. 只更新传入的字段（PATCH 语义）
    4. 返回更新后的完整用户信息

    Args:
        profile_update: 用户资料更新数据（所有字段可选）

    Returns:
        更新后的用户对象

    Raises:
        HTTPException 409: 当新邮箱已被其他用户占用时
    """
    try:
        updated_user = crud_user.update_profile(
            db=db, user=current_user, profile_update=profile_update
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="邮箱已被其他用户占用"
        ) from e


@router.put("/me/password")
def change_password(
    *,
    db: Session = Depends(get_db),
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """
    修改当前用户密码

    安全要点：
    1. 必须验证旧密码正确性（防止会话劫持）
    2. 使用 bcrypt 哈希存储新密码
    3. 不返回任何敏感信息

    Args:
        password_change: 密码修改请求（包含旧密码和新密码）

    Returns:
        成功消息

    Raises:
        HTTPException 400: 当旧密码不正确时
        HTTPException 422: 当新密码不符合格式要求时（Pydantic 自动处理）
    """
    try:
        crud_user.update_password(
            db=db,
            user=current_user,
            old_password=password_change.old_password,
            new_password=password_change.new_password,
        )

        return {"message": "密码修改成功"}
    except ValueError as e:
        # ✅ 保留原始错误信息，提供更好的用户体验
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",  # 来自 CRUD 层的错误信息
        ) from e
