import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class PostLike(Base):
    """
    文章点赞模型

    设计要点：
    1. 使用 UUID 主键，与项目其他模型保持一致
    2. 用户删除时保留点赞记录（保护统计数据准确性）
    3. 文章删除时清理点赞记录（文章不存在则统计无意义）
    4. 唯一约束防止同一用户重复点赞同一文章
    """

    __tablename__ = "post_likes"

    # 1. 主键
    id: Mapped[UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        comment="点赞记录唯一标识符",
    )

    # 2. 关联外键：用户ID
    # 用户删除时保留点赞记录（保护统计数据准确性）
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        comment="点赞用户ID（用户删除后为空）",
    )

    # 3. 关联外键：文章ID
    # 文章删除时清理点赞记录（文章不存在则统计无意义）
    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        index=True,
        comment="点赞文章ID",
    )

    # 4. 点赞时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="点赞时间",
    )

    # 联合唯一索引: 用户ID和文章ID
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_likes_user_post"),
    )

    # 5.关系定义
    # PostLike → User: 多对一(不指定 lazy策略，由应用层在需要时显式加载)
    user: Mapped["User | None"] = relationship(
        back_populates="post_likes",
        # lazy="joined", # 查询点赞记录时通常需要用户信息
    )

    # PostLike → Post: 多对一(不指定 lazy策略，由应用层在需要时显式加载)
    post: Mapped["Post"] = relationship(
        back_populates="likes",
        # lazy="joined", # 查询点赞记录时通常需要文章信息
    )

    def __repr__(self) -> str:
        """为开发者提供一个无歧义的、可调试的字符串表示。"""
        return (
            f"<PostLike(id={self.id}, user_id={self.user_id}, post_id={self.post_id})>"
        )

    def __str__(self) -> str:
        """提供一个用户友好的、具有业务含义的字符串表示。"""
        # 1. 处理用户信息：如果 self.user 对象存在，则使用其用户名；
        #    否则，表示这是一个已删除用户的点赞。
        user_info = self.user.username if self.user else "A deleted user"

        # 2. 处理文章信息：因为 Post 删除会级联删除 PostLike，
        #    所以 self.post 在这里可以安全地假定总是存在的。
        post_info = f"'{self.post.title}'"

        return f"{user_info} liked {post_info}"
