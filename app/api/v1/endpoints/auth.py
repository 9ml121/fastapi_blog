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

import random
import string
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.db.redis_client import save_verification_code
from app.schemas.user import UserAuthResponse, UserCreate

# 创建路由器
router = APIRouter()


# ============================= 发送邮箱验证码 ===========================
@router.post("/send-code")
async def send_verification_code(
    email: EmailStr = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """发送邮箱验证码

    **权限**: 公开访问

    **请求体**:
    - email: 邮箱地址

    **返回**:
    - 200: 验证码发送成功
    - 400: 邮箱已被注册
    """
    # 1. 检查邮箱是否已注册
    existing_user = user_crud.get_user_by_email(db, email=email)
    if existing_user:
        raise EmailAlreadyExistsError(email=email)

    # 2. 生成 6 位随机验证码
    code = "".join(random.choices(string.digits, k=6))

    # 3. 存储验证码到 Redis
    save_verification_code(email=email, code=code)

    # todo 4.发送验证码邮件
    print(f"发送验证码 {code} 到邮箱 {email}（模拟）")

    return {"message": "验证码已发送，请查收邮件"}


# ============================= 用户注册 ===========================
@router.post(
    "/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """用户注册（注册成功自动登录）

    **权限**: 公开访问，无需登录

    **请求体**:
    - UserCreate: 用户注册数据（email, password, verification_code）

    **返回**:
    - 201: 注册成功，返回访问令牌和用户信息

    **示例**:
        POST /api/v1/auth/register
        {
            "email": "john@example.com",
            "password": "securepassword",
            "verification_code": "123456"
        }
    """
    # 1. 调用 CRUD 创建用户 (内部会处理验证码校验和用户名生成)
    user = user_crud.create_user(db, user_in=user_data)

    # 2. 注册成功，立即为该用户签发 Token (实现自动登录)
    settings = get_settings()
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # 3. 组装返回数据
    # # 这里的 user 是 ORM 对象，FastAPI 会自动根据 UserResponse 的定义进行序列化
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }  # type: ignore


# ============================= 用户登录 ===========================
@router.post("/login", response_model=UserAuthResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember: bool = Form(default=False),
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """用户登录

    **权限**: 公开访问，无需登录

    **请求体** (Form Data):
    - username: 用户名或邮箱,目前前端只支持邮箱注册
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
    user = user_crud.authenticate_user(
        db, identifier=form_data.username, password=form_data.password
    )

    if not user:
        raise InvalidCredentialsError()

    settings = get_settings()
    if remember:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER
    else:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    # 生成 JWT access token
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(minutes=expires_minutes)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }  # type: ignore
