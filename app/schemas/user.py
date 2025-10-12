"""
User Pydantic Schemas - 用户数据验证和序列化

设计思路：
1. UserBase: 提取公共字段，供其他 Schema 继承
2. UserCreate: 用户注册时的输入数据（包含密码）
3. UserUpdate: 用户更新时的输入数据（所有字段可选）
4. UserResponse: 返回给客户端的数据（排除敏感字段）
5. UserInDB: 内部使用的完整数据（包含敏感字段）
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ============ 密码配置常量 ============
MIN_PASSWORD_LENGTH = 8
PASSWORD_DESCRIPTION = f"密码，至少{MIN_PASSWORD_LENGTH}个字符且必须包含字母和数字"


# ============ 公共验证函数 ============


def validate_password_complexity(password: str) -> str:
    """
    公共密码复杂度验证

    统一密码验证规则，避免代码重复，遵循 DRY 原则。

    验证规则：
    - 至少8个字符
    - 包含至少一个数字
    - 包含至少一个字母

    Args:
        password: 待验证的密码字符串

    Returns:
        验证通过的密码字符串

    Raises:
        ValueError: 当密码不符合复杂度要求时
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"密码必须至少{MIN_PASSWORD_LENGTH}个字符")
    if not any(char.isdigit() for char in password):
        raise ValueError("密码必须包含至少一个数字")
    if not any(char.isalpha() for char in password):
        raise ValueError("密码必须包含至少一个字母")
    return password


# ============ 基类 ============
class UserBase(BaseModel):
    """
    用户基础字段

    提取公共字段供其他 Schema 继承，遵循 DRY 原则
    """

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="用户名，3-50个字符，只允许字母、数字、下划线",
        examples=["johndoe", "user_123", "alice2024"],
    )
    email: EmailStr = Field(
        description="邮箱地址，用于登录和通知",
        examples=["john@example.com"],
    )
    nickname: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="用户昵称，将显示在文章和评论中",
        examples=["张三", "John Doe", "🎉 Happy User"],
    )


# ============ 创建 Schema ============
class UserCreate(UserBase):
    """
    用户注册时的输入数据

    特点：
    - 继承 UserBase 的所有字段
    - 额外包含 password（明文，仅在创建时需要）
    - 所有字段都是必填的（除了 full_name）

    用途：POST /api/v1/auth/register
    """

    password: str = Field(
        min_length=MIN_PASSWORD_LENGTH,
        max_length=100,
        description=PASSWORD_DESCRIPTION,
        examples=["SecurePass123"],
    )

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """自定义密码复杂度验证"""
        return validate_password_complexity(v)

    # 为自动生成 API 的数据模型文档设置示例值
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "nickname": "张三",
                    "password": "SecurePass123",
                }
            ]
        }
    )


# ============ 更新 Schema ============
# ⚠️ Update模型一般是直接继承 BaseModel, 不能继承 UserBase!
class UserProfileUpdate(BaseModel):
    """用户自主更新个人资料

    特点：
    - 所有字段都是可选的（支持部分更新）
    - 只允许用户修改自己的基本信息（nickname, email）
    - 不包含权限相关字段（is_active 等）
    - 不包含密码修改（使用单独端点）

    用途：PATCH /api/v1/users/me（用户自主更新）
    """

    nickname: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="用户昵称，将显示在文章和评论中",
        examples=["张三", "John Doe", "🎉 Happy User"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="邮箱地址，用于登录和通知",
        examples=["john@example.com"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nickname": "张三 Updated",
                    "email": "zhangsan@example.com",
                }
            ]
        }
    )


class UserUpdate(BaseModel):
    """管理员更新用户信息

    特点：
    - 所有字段都是可选的（支持部分更新）
    - 管理员可以更新用户的所有基本信息
    - 包含权限相关字段（is_active）
    - 不包含密码修改（使用单独端点）

    用途：PATCH /api/v1/users/{user_id}（管理员更新，Phase 6 实现）
    """

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="用户名，3-50个字符，只允许字母、数字、下划线",
    )
    email: EmailStr | None = Field(
        default=None,
        description="邮箱地址",
    )
    nickname: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="用户昵称",
    )
    is_active: bool | None = Field(
        default=None,
        description="用户是否激活（管理员功能）",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nickname": "John Doe Updated",
                    "is_active": True,
                }
            ]
        }
    )


class PasswordChange(BaseModel):
    """密码修改请求模型

    特点：
    - 必须提供旧密码（安全验证）
    - 新密码有基本长度要求
    - 可扩展密码强度验证

    用途：PUT /api/v1/users/me/password
    """

    old_password: str = Field(
        ...,  # 必填字段
        min_length=1,
        description="当前密码，用于验证身份",
        examples=["OldPassword123!"],
    )
    new_password: str = Field(
        ...,  # 必填字段
        min_length=MIN_PASSWORD_LENGTH,
        max_length=100,
        description=PASSWORD_DESCRIPTION,
        examples=["NewPassword456!"],
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证新密码强度（基础验证）"""
        return validate_password_complexity(v)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "old_password": "OldPassword123!",
                    "new_password": "NewPassword456!",
                }
            ]
        }
    )


# ============ 响应 Schema ============
class UserResponse(UserBase):
    """
    返回给客户端的用户数据

    特点：
    - 继承 UserBase 的所有字段（username, email, nickname）
    - 额外包含系统生成的字段（id, created_at, updated_at）
    - 包含业务状态字段（is_active, role, is_verified）
    - 包含 UI 相关字段（avatar, last_login）
    - ⚠️ 不包含敏感和隐私字段（password_hash-密码哈希, deleted_at-软删除时间）

    用途：所有返回用户信息的 API
    """

    id: UUID = Field(description="用户唯一标识")
    is_active: bool = Field(description="用户是否激活")
    role: str = Field(description="用户角色（user/admin），用于前端 UI 控制")
    avatar: str | None = Field(
        default=None, description="用户头像路径，前端显示头像使用"
    )
    is_verified: bool = Field(description="邮箱是否已验证，用于提醒用户完成邮箱验证")
    last_login: datetime | None = Field(
        default=None, description="最后登录时间，用于安全提醒（异常登录检测）"
    )
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")

    # 配置：允许从 ORM 对象创建（重要！）
    model_config = ConfigDict(
        from_attributes=True,  # 允许从 SQLAlchemy 模型创建
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "nickname": "张三",
                    "is_active": True,
                    "role": "user",
                    "avatar": "/avatars/johndoe.jpg",
                    "is_verified": True,
                    "last_login": "2024-01-15T10:30:00Z",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ]
        },
    )


# ============ 内部 Schema ============
class UserInDB(UserResponse):
    """
    内部使用的完整用户数据

    特点：
    - 继承 UserResponse 的所有字段
    - 额外包含敏感字段（password_hash）
    - 包含软删除字段（deleted_at）
    - 仅在内部业务逻辑中使用，绝不返回给客户端

    用途：CRUD 层内部操作、权限检查
    """

    password_hash: str = Field(description="密码哈希值")
    deleted_at: datetime | None = Field(
        default=None, description="软删除时间（NULL 表示未删除）"
    )

    model_config = ConfigDict(from_attributes=True)
