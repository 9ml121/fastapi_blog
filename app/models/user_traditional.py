"""
用户模型 - 传统 SQLAlchemy Core 语法版本

⚠️  注意：此文件仅用于学习对比传统语法与现代语法的差异
🚀 项目中请使用 user.py (现代语法版本)

此版本展示了传统的 SQLAlchemy Core 层语法：
- 使用 Column() 定义字段
- 没有类型注解
- 可空性通过 nullable 参数控制
"""

import uuid
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.database import Base


class UserRole(str, Enum):
    """
    用户角色枚举

    继承 str 是为了让枚举值可以直接序列化为 JSON
    这对 FastAPI 的自动文档生成很有帮助
    """

    USER = "user"  # 普通用户
    ADMIN = "admin"  # 管理员


class UserTraditional(Base):
    """
    用户模型 - 传统语法版本

    设计要点：
    1. 使用 UUID 作为主键，支持分布式系统
    2. 支持用户名和邮箱双重登录方式
    3. 密码只存储哈希值，不存储明文
    4. 使用枚举类型管理用户角色
    5. 包含软删除和邮箱验证功能

    ⚠️ 传统语法特点：
    - 使用 Column() 定义字段
    - 没有 Mapped[Type] 类型注解
    - IDE 支持有限，无类型提示
    """

    __tablename__ = "users_traditional"

    def __init__(self, **kwargs):
        """初始化用户实例，设置默认值"""
        kwargs.setdefault("role", UserRole.USER)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_verified", False)
        super().__init__(**kwargs)

    # 主键：使用 UUID 保证全局唯一性
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="用户唯一标识")

    # 登录凭证
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名（唯一）")

    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱地址（唯一）")

    password_hash = Column(String(255), nullable=False, comment="密码哈希值")

    # 基本信息
    nickname = Column(String(50), nullable=False, comment="显示昵称")

    avatar = Column(String(255), nullable=True, comment="头像文件路径")

    # 权限和状态
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER, comment="用户角色") # type: ignore

    is_active = Column(Boolean, nullable=False, default=True, comment="账户是否激活（软删除标记）")

    is_verified = Column(Boolean, nullable=False, default=False, comment="邮箱是否已验证")

    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="创建时间")

    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    last_login = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")

    def __repr__(self) -> str:
        """字符串表示，用于调试"""
        return f"<UserTraditional(id={self.id}, username='{self.username}', role='{self.role}')>"

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"{self.nickname} (@{self.username})"

    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        # 显式转换为 bool 以满足 mypy 的静态类型检查。
        # SQLAlchemy 的比较运算在某些上下文中返回 ColumnElement，而非纯 bool。
        return bool(self.role == UserRole.ADMIN)

    @property
    def is_regular_user(self) -> bool:
        """检查是否为普通用户"""
        # 显式转换为 bool 以满足 mypy 的静态类型检查。
        return bool(self.role == UserRole.USER)

    def activate(self):
        """激活用户账户"""
        self.is_active = True

    def deactivate(self):
        """停用用户账户（软删除）"""
        self.is_active = False

    def verify_email(self):
        """标记邮箱为已验证"""
        self.is_verified = True

    def promote_to_admin(self):
        """提升为管理员"""
        self.role = UserRole.ADMIN

    def demote_to_user(self):
        """降级为普通用户"""
        self.role = UserRole.USER
