"""
认证相关的 API 端点

提供用户注册、登录、获取当前用户信息等功能
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

# 创建路由器
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,  # ← Pydantic 自动验证
    db: Session = Depends(get_db),  # ← 依赖注入数据库会话
) -> Any:
    """用户注册

    注册流程:
    1. 验证邮箱未被注册
    2. 验证用户名未被使用
    3. 创建用户(密码自动哈希)
    4. 返回用户信息(排除密码)
    """
    # 检查邮箱是否已存在
    existing_user = crud_user.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    # 检查用户名是否已存在
    existing_username: User | None = crud_user.get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被使用",
        )

    # 创建用户(密码会在 CRUD 层自动哈希)
    new_user: User = crud_user.create_user(db, user_in=user_data)

    return new_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    """
    用户登录

    登录流程:
    1. 验证用户名和密码
    2. 生成 JWT access token
    3. 返回 token(用于后续请求认证)
    """
    # 认证用户(CRUD 层会防止时序攻击)
    user = crud_user.authenticate_user(db, identifier=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},  # OAuth2 规范要求
        )

    # 生成 JWT access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取当前用户信息

    需要在 Header 中提供有效的 JWT token:
    Authorization: Bearer <access_token>
    """
    return current_user
