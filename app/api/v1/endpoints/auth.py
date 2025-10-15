"""
认证相关的 API 端点

提供用户注册、登录等功能

知识点：
1. Swagger UI 是 FastAPI 的杀手级功能：自动生成交互式 API 文档，
   点击"Try it out"就能测试API，比看代码快10倍！访问 http://localhost:8000/docs 即可。
2. Pydantic Schema 是 API 契约：Schema 定义了前后端的数据格式约定，
   是API文档的单一数据源（Single Source of Truth）。
3. Depends() 表示"自动注入"：凡是看到 = Depends()，说明这个参数不需要客户端传递，
   FastAPI 会自动处理（数据库会话、当前用户等）。
4. OAuth2PasswordRequestForm 的特殊性：它要求 Form Data
   （application/x-www-form-urlencoded），不是JSON！这是OAuth2标准规定的。
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
)
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

# 创建路由器
router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """用户注册

    **权限**: 公开访问，无需登录

    **请求体**:
    - UserCreate: 用户注册数据（用户名、邮箱、密码等）

    **返回**:
    - 201: 用户注册成功
    - 400: 邮箱或用户名已存在
    - 422: 请求数据无效

    **示例**:
        POST /api/v1/auth/register
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "securepassword",
            "nickname": "John Doe"
        }
    """
    # 检查邮箱是否已存在
    existing_user = crud_user.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise EmailAlreadyExistsError(email=user_data.email)

    # 检查用户名是否已存在
    existing_username: User | None = crud_user.get_user_by_username(
        db, username=user_data.username
    )
    if existing_username:
        raise UsernameAlreadyExistsError(username=user_data.username)

    # 创建用户(密码会在 CRUD 层自动哈希)
    new_user: User = crud_user.create_user(db, user_in=user_data)

    return new_user  # type: ignore


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """用户登录

    **权限**: 公开访问，无需登录

    **请求体** (Form Data):
    - username: 用户名或邮箱
    - password: 密码

    **返回**:
    - 200: 登录成功，返回 access_token
    - 401: 用户名或密码错误

    **示例**:
        POST /api/v1/auth/login
        Content-Type: application/x-www-form-urlencoded

        username=johndoe&password=securepassword
    """
    # 认证用户(CRUD 层会防止时序攻击)
    user = crud_user.authenticate_user(
        db, identifier=form_data.username, password=form_data.password
    )

    if not user:
        raise InvalidCredentialsError()

    # 生成 JWT access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
