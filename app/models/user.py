"""
用户模型 - 现代 SQLAlchemy 2.0+ 语法版本

🆕 现代语法特点：
    - 使用 Mapped[Type] 类型注解
    - 使用 mapped_column() 替代 Column()
    - 类型更明确，IDE 支持更好
    - Optional[Type] 明确表示可空字段

🚀 项目正式使用版本 - 采用现代声明式映射语法
📚 与 user_traditional.py 对比学习传统语法差异
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

# 使用 TYPE_CHECKING 避免循环导入
# 仅在类型检查时导入，运行时不导入
# 参考：https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#adding-relationships-to-mapped-classes-after-declaration
if TYPE_CHECKING:
    from .comment import Comment
    from .follow import Follow
    from .notification import Notification
    from .post import Post, PostView
    from .post_favorite import PostFavorite
    from .post_like import PostLike


class UserRole(str, Enum):
    """用户角色枚举

    继承 str 是为了让枚举值可以直接序列化为 JSON
    这对 FastAPI 的自动文档生成很有帮助
    """

    USER = "user"  # 普通用户
    ADMIN = "admin"  # 管理员


class User(Base):
    """users数据库表模型

    设计要点：
    1. 使用 UUID 作为主键，支持分布式系统
    2. 支持用户名和邮箱双重登录方式
    3. 密码只存储哈希值，不存储明文
    4. 使用枚举类型管理用户角色
    5. 包含软删除和邮箱验证功能
    6. 与 Post, Comment, PostView, PostLike, PostFavorite 等模型建立关联关系
    """

    __tablename__ = "users"

    def __init__(self, **kwargs):
        """初始化用户实例，只处理需要计算或有复杂的业务逻辑默认值，
        简单的固定默认值通过 mapped_column(default=...) 设置
        """
        # 如果没有提供昵称，使用用户名作为昵称
        if not kwargs.get("nickname") and "username" in kwargs:
            kwargs["nickname"] = kwargs["username"]

        super().__init__(**kwargs)

    # 1. 主键
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, comment="用户唯一标识"
    )

    # 2. 核心业务字段 - 登录凭证
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="用户名（唯一）"
    )

    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, comment="邮箱地址（唯一）"
    )

    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希值")

    # 基本信息
    nickname: Mapped[str] = mapped_column(String(50), comment="显示昵称")

    avatar: Mapped[str | None] = mapped_column(
        String(255), default=None, comment="头像文件路径"
    )

    bio: Mapped[str | None] = mapped_column(
        String(255), default=None, comment="个人简介，用于在用户个人主页展示"
    )

    # 3. 状态和配置字段 - 配置
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, comment="用户角色"
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="账户是否激活（管理员可禁用）"
    )

    # 状态
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="邮箱是否已验证"
    )

    # 4. 时间戳字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, comment="最后登录时间"
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, comment="软删除时间（用户主动删除账号）"
    )

    # ============== 5. 关系定义 ==============
    # User → Post： 一对多(用户发布文章)
    # ⚠️ lazy="select" 是默认值，这里先不指定，在应用层按需加载（一对多用 selectin）
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    # User → Comment: 一对多(用户发表评论)
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

    # User → PostView: 一对多(用户浏览记录)
    post_views: Mapped[list["PostView"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",  # 删除用户时删除其浏览记录
        order_by="desc(PostView.viewed_at)",  # 按浏览时间倒序
    )

    # User → PostLike: 一对多(用户点赞记录)
    post_likes: Mapped[list["PostLike"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(PostLike.created_at)",
    )

    # User → PostFavorite: 一对多(用户收藏记录)
    post_favorites: Mapped[list["PostFavorite"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(PostFavorite.created_at)",
    )

    # User → Follow: 一对多(用户关注关系)
    followers: Mapped[list["Follow"]] = relationship(
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
        order_by="desc(Follow.created_at)",
    )
    following: Mapped[list["Follow"]] = relationship(
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
        order_by="desc(Follow.created_at)",
    )

    # User → Notification: 一对多(用户通知关系)
    received_notifications: Mapped[list["Notification"]] = relationship(
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        cascade="all",
        order_by="desc(Notification.created_at)",
    )
    sent_notifications: Mapped[list["Notification"]] = relationship(
        foreign_keys="Notification.actor_id",
        back_populates="actor",
        cascade="all",
    )

    def __repr__(self) -> str:
        """开发调试用的字符串表示"""
        return (
            f"<User(id={self.id}, username='{self.username}',"
            f"role='{self.role}', email='{self.email}', "
            f"last_login='{self.last_login})>"
        )

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"{self.nickname} (@{self.username})"

    # 业务状态检查属性
    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN

    @property
    def is_regular_user(self) -> bool:
        """检查是否为普通用户"""
        return self.role == UserRole.USER

    @property
    def display_name(self) -> str:
        """显示名称（昵称优先，用户名备用）"""
        return self.nickname or self.username

    # 业务操作方法
    def activate(self) -> None:
        """激活用户账户"""
        self.is_active = True

    def deactivate(self) -> None:
        """停用用户账户（软删除）"""
        self.is_active = False

    def verify_email(self) -> None:
        """标记邮箱为已验证"""
        self.is_verified = True

    def promote_to_admin(self) -> None:
        """提升为管理员"""
        self.role = UserRole.ADMIN

    def demote_to_user(self) -> None:
        """降级为普通用户"""
        self.role = UserRole.USER

    def update_last_login(self) -> None:
        """更新最后登录时间"""
        self.last_login = datetime.now(UTC)
