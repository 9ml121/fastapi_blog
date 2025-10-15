"""
API 依赖项 - FastAPI 依赖注入函数

本模块提供认证和数据库相关的依赖函数，用于 FastAPI 路由的依赖注入。

依赖层次：
1. get_db()                  - 数据库会话（基础依赖）
2. get_current_user()        - 从 token 获取用户（认证依赖）
3. get_current_active_user() - 验证用户活跃状态（业务依赖）
4. get_current_superuser()   - 验证管理员权限（权限依赖）

设计原则：
- 单一职责：每个依赖只负责一个验证步骤
- 最小权限：接口只使用必要的依赖
- 资源管理：使用 yield 确保资源清理
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import crud
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

# ==========================================
# OAuth2 配置
# ==========================================

# OAuth2 密码流程（从 Authorization header 提取 token）
# tokenUrl 指向登录接口，用于 Swagger 文档生成"登录"按钮
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# ==========================================
# 认证依赖：用户身份验证
# ==========================================


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户依赖（任何状态的用户）

    工作流程：
    1. 从 Authorization header 提取 token（oauth2_scheme 自动处理）
    2. 解码 JWT token，验证签名和过期时间
    3. 从 payload 提取用户 ID（sub 字段）
    4. 从数据库查询用户
    5. 返回用户对象

    Args:
        token: JWT token（由 oauth2_scheme 自动从请求头提取）
        db: 数据库会话（由 get_db 依赖注入）

    Returns:
        User: 当前登录用户对象（包括禁用用户）

    Raises:
        HTTPException 401: token 无效、过期、用户不存在等

    示例：
        @app.get("/me")
        def read_current_user(current_user: User = Depends(get_current_user)):
            return current_user

    注意：
    - 此依赖不检查用户状态（is_active），只验证 token 有效性
    - 如需验证用户状态，使用 get_current_active_user
    """
    # 1. 解码 token
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Could not validate credentials")

    # 2. 从 payload 提取用户 ID（JWT 标准使用 sub 字段）
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    # 3. 转换 user_id 为 UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError as err:
        raise UnauthorizedError("Invalid user ID format") from err

    # 4. 从数据库查询用户
    user = crud.user.get_user_by_id(db, user_id=user_id)
    if not user:
        raise UnauthorizedError("User not found")

    return user


# ==========================================
# 业务依赖：活跃用户验证
# ==========================================


def get_current_active_user(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> User:
    """
    获取当前活跃用户依赖（验证用户状态）

    工作流程：
    1. 通过 get_current_user 获取登录用户
    2. 检查用户是否活跃（is_active == True）
    3. 返回活跃用户

    Args:
        current_user: 当前登录用户（由 get_current_user 依赖注入）

    Returns:
        User: 活跃的用户对象

    Raises:
        HTTPException 400: 用户账户已禁用

    示例：
        @app.post("/posts")
        def create_post(current_user: User = Depends(get_current_active_user)):
            # 只有活跃用户可以发表文章
            ...

    注意：
    - 用于需要用户活跃才能执行的业务操作（发文章、评论等）
    - 禁用用户无法通过此依赖
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


# ==========================================
# 权限依赖：管理员权限验证
# ==========================================


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),  # noqa: B008
) -> User:
    """
    获取当前管理员用户依赖（验证管理员权限）

    工作流程：
    1. 通过 get_current_active_user 获取活跃用户
    2. 检查用户是否为管理员（is_admin == True）
    3. 返回管理员用户

    Args:
        current_user: 当前活跃用户（由 get_current_active_user 依赖注入）

    Returns:
        User: 管理员用户对象

    Raises:
        HTTPException 403: 用户权限不足

    示例：
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: UUID,
            current_user: User = Depends(get_current_superuser)
        ):
            # 只有管理员可以删除用户
            ...

    注意：
    - 用于需要管理员权限的操作（删除用户、审核内容等）
    - 普通用户会收到 403 Forbidden 错误
    - 依赖 get_current_active_user，确保管理员账户也是活跃的
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
