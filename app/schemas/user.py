"""
User Schemas - 用户数据验证和序列化

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
        min_length=8,
        max_length=100,
        description="密码，至少8个字符，且必须包含字母和数字",
        examples=["SecurePass123"],
    )

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """自定义密码复杂度验证"""
        if not any(char.isdigit() for char in v):
            raise ValueError("密码必须包含至少一个数字")
        if not any(char.isalpha() for char in v):
            raise ValueError("密码必须包含至少一个字母")
        return v

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
class UserUpdate(BaseModel):
    """
    用户更新时的输入数据

    特点：
    - 所有字段都是可选的（支持部分更新）
    - 不包含不允许修改的字段（如 id, created_at）

    用途：PATCH /api/v1/users/{user_id}
    ⚠️ 这里是直接继承 BaseModel, 不能继承 UserBase，存在部分代码重复
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

    # ⚠️ TODO: 临时方案 - 未来应该使用单独的密码更新端点
    # 原因：
    # 1. 密码修改应该验证旧密码（安全考虑）
    # 2. 应该与普通信息更新分离（单一职责原则）
    # 3. 可能需要二次验证（邮箱/短信）
    # 未来改进：
    # - 创建 PasswordUpdate schema（包含 old_password + new_password）
    # - 创建单独的 API 端点 POST /users/{id}/password
    # - 实现完整的密码修改流程（验证旧密码、发送通知等）
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="新密码（临时方案：未来应使用单独的密码更新端点）",
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


# ============ 响应 Schema ============
class UserResponse(UserBase):
    """
    返回给客户端的用户数据

    特点：
    - 继承 UserBase 的所有字段
    - 额外包含系统生成的字段（id, created_at, updated_at）
    - 包含业务状态字段（is_active）
    - 不包含敏感字段（password_hash, is_superuser, deleted_at）

    用途：所有返回用户信息的 API
    """

    id: UUID = Field(description="用户唯一标识")
    is_active: bool = Field(description="用户是否激活")
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
    - 额外包含敏感字段（password_hash, is_superuser）
    - 包含软删除字段（deleted_at）
    - 仅在内部业务逻辑中使用，绝不返回给客户端

    用途：CRUD 层内部操作、权限检查
    """

    password_hash: str = Field(description="密码哈希值")
    is_superuser: bool = Field(description="是否为超级管理员")
    deleted_at: datetime | None = Field(default=None, description="软删除时间（NULL 表示未删除）")

    model_config = ConfigDict(from_attributes=True)
