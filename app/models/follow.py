import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .user import User


class Follow(Base):
    """用户关注关系模型"""

    __tablename__ = "follows"

    # 主键
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # 关键字段
    follower_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关注者ID"
    )
    followed_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="被关注者ID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="关注时间"
    )

    # 索引优化
    __table_args__ = (
        # 唯一约束：防止重复关注
        UniqueConstraint("follower_id", "followed_id", name="uq_follow_unique"),
        # 索引：查询某用户的粉丝列表
        Index("idx_followed_created", "followed_id", "created_at"),
        # 索引：查询某用户的关注列表
        Index("idx_follower_created", "follower_id", "created_at"),
    )

    # 关系映射
    # Follow → User: 多对一(用户关注关系)
    follower: Mapped["User"] = relationship(
        foreign_keys=[follower_id],
        back_populates="following",
        lazy="joined",
    )

    followed: Mapped["User"] = relationship(
        foreign_keys=[followed_id],
        back_populates="followers",
        lazy="joined",
    )
