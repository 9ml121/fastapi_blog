"""
Comment 模型 - 评论系统

实现功能：
- 用户评论文章
- 评论回复评论（层级结构）
- 评论审核和软删除
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class Comment(Base):
    """
    评论模型 - 支持层级评论结构

    核心特性：
    1. 自引用关系 - 评论可以回复评论
    2. 软删除 - 标记删除而不是真正删除
    3. 审核机制 - 评论需要审核才能公开显示
    """

    __tablename__ = "comments"

    # ============ 主键 ============
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # ============ 核心字段 ============
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容")

    # ============ 外键关系 ============
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="评论作者 ID",
    )

    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属文章 ID",
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="父评论 ID（顶级评论为 None）",
    )

    # ============ 状态管理字段 ============
    is_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否审核通过"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="软删除标记"
    )

    # ============ 时间戳 ============
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # ============ 关系映射 ============
    # 自引用关系 - 评论的父子结构
    # Comment → parent Comment: 一对一
    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        remote_side=[id],  # ⭐ 关键：指定"远端"是 id 字段
        back_populates="replies",
    )

    # Comment → replies Comment: 一对多
    # ⚠️ lazy="select" 是默认值，可以先不指定，
    # 以后按需查询replies列表在指定（一对多用 selectin）
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",  # 删除评论时级联删除子评论
    )

    # Comment → User：多对一（多条评论 → 一个作者）
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments",
        lazy="joined",  # 显示评论列表时几乎总要显示"谁评论的"
    )

    # Comment → Post：多对一（多条评论 → 一篇文章）
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments",
        lazy="joined",  # 适合"消息中心"场景
    )

    # ============ 业务方法 ============
    def approve(self) -> None:
        """审核通过评论"""
        self.is_approved = True

    def soft_delete(self) -> None:
        """软删除评论（标记为已删除，不从数据库移除）"""
        self.is_deleted = True

    def restore(self) -> None:
        """恢复已软删除的评论"""
        self.is_deleted = False

    # ============ 属性方法 ============
    @property
    def is_top_level(self) -> bool:
        """是否为顶级评论（直接回复文章的评论）"""
        return self.parent_id is None

    @property
    def reply_count(self) -> int:
        """获取直接回复此评论的数量"""
        return len(self.replies)

    # ============ 字符串表示 ============
    def __repr__(self) -> str:
        """开发调试用的字符串表示"""
        return (
            f"<Comment(id={self.id}, "
            f"author_id={self.user_id}, "
            f"post_id={self.post_id}, "
            f"is_approved={self.is_approved}, >"
            f"parent_id={self.parent_id})>"
        )
