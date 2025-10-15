"""
用户资料管理 API 端点

提供用户个人资料的查看、更新和密码修改功能。

设计要点：
1. 使用 /users/me 端点：安全、语义化，避免用户通过修改 URL 访问他人资料
2. PATCH vs PUT 语义区分：PATCH 用于部分更新（用户资料），PUT 用于完整替换（密码修改）
3. 职责分离：普通用户用 UserProfileUpdate，管理员用 UserUpdate（Phase 6 实现）
4. 安全验证：密码修改必须验证旧密码，防止会话劫持
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import EmailAlreadyExistsError, InvalidPasswordError
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import PasswordChange, UserProfileUpdate, UserResponse

# 创建路由器 - 前缀 /users 已在 main.py 中配置
router = APIRouter()


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


@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
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
    try:
        updated_user = crud_user.update_profile(
            db=db, user=current_user, profile_update=profile_update
        )
        return updated_user  # type: ignore
    except ValueError as e:
        raise EmailAlreadyExistsError(email=profile_update.email or "") from e


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
    try:
        crud_user.update_password(
            db=db,
            user=current_user,
            old_password=password_change.old_password,
            new_password=password_change.new_password,
        )

        return {"message": "密码修改成功"}
    except ValueError as e:
        raise InvalidPasswordError() from e
