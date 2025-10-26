import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class PostFavorite(Base):
    """
    文章收藏模型

    设计要点：
    1. 使用 UUID 主键，与项目其他模型保持一致
    2. 用户删除时保留收藏记录（保护统计数据准确性）
    3. 文章删除时清理收藏记录（文章不存在则统计无意义）
    4. 唯一约束防止同一用户重复收藏同一文章
    """

    __tablename__ = "post_favorites"

    # 1. 主键
    id: Mapped[UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        comment="收藏记录唯一标识符",
    )

    # 关联外键：用户ID
    # 用户删除时保留收藏记录（保护统计数据准确性）
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        comment="收藏用户ID",
    )

    # 关联外键：文章ID
    # 文章删除时收藏记录删除
    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        index=True,
        comment="收藏文章ID",
    )

    # 收藏时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="收藏时间",
    )

    # 联合唯一索引: 用户ID和文章ID
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_favorites_user_post"),
    )

    # 关系定义
    # PostFavorite → User: 多对一
    user: Mapped["User | None"] = relationship(
        back_populates="post_favorites",
        # lazy="joined",  # 查询收藏记录时通常需要用户信息
    )

    # PostFavorite → Post: 多对一
    post: Mapped["Post"] = relationship(
        back_populates="favorites",
        # lazy="joined",  # 查询收藏记录时通常需要文章信息
    )

    def __repr__(self) -> str:
        """为开发者提供一个无歧义的、可调试的字符串表示。"""
        return (
            f"<PostFavorite(id={self.id}, user_id={self.user_id},"
            f"post_id={self.post_id})>"
        )

    def __str__(self) -> str:
        """提供一个用户友好的、具有业务含义的字符串表示。"""
        user_info = self.user.username if self.user else "A deleted user"
        post_info = f"'{self.post.title}'"

        return f"{user_info} favorited {post_info}"
