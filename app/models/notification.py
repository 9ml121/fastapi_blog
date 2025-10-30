import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .post import Post
    from .user import User


class NotificationType(str, Enum):
    """通知类型枚举 LIKE | COMMENT | FOLLOW"""

    LIKE = "like"  # 点赞
    COMMENT = "comment"  # 评论
    FOLLOW = "follow"  # 关注
    # 后续可扩展：REPLY = "reply", MENTION = "mention" 等


class Notification(Base):
    """通知记录模型"""

    __tablename__ = "notifications"

    # Notification 模型临时字段
    if TYPE_CHECKING:
        message: str

    # 主键
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # 关键字段
    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="通知接收人ID"
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), comment="操作发起人ID"
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType), comment="通知类型：like, comment, follow"
    )

    # 关联资源（可选，根据通知类型）
    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联的文章ID（点赞、评论类通知）",
    )
    comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联的评论ID（仅评论通知）",
    )

    # 聚合字段（核心设计）
    aggregated_count: Mapped[int] = mapped_column(
        Integer, default=1, comment="聚合操作数（同一资源1小时内的多个操作合并为1条）"
    )

    # 状态字段
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="是否已读"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="通知创建时间",
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="通知最后更新时间（用于聚合判断，1小时内视为同一批操作）",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="标记已读的时间"
    )

    # 索引优化查询性能
    __table_args__ = (
        # 查询用户的所有通知（按创建时间倒序）
        Index("idx_recipient_created", "recipient_id", "created_at"),
        # 查询用户的未读通知（加速频繁的未读查询）
        Index("idx_recipient_unread", "recipient_id", "is_read", "created_at"),
        # 去重检查：同一资源的通知（用于聚合判断）
        # 注意：移除了 actor_id 限制，支持多用户操作的聚合
        # 一条父评论只对应一条通知
        UniqueConstraint(
            "recipient_id",
            "post_id",
            "comment_id",
            "notification_type",
            name="uq_notification_unique",
        ),
    )

    # ============================= 关系映射 =============================
    # notification → user: 多对一(通知消息对应的发起人和接收人关系)
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id],
        back_populates="received_notifications",
    )

    actor: Mapped["User"] = relationship(
        foreign_keys=[actor_id],
        back_populates="sent_notifications",
    )

    # notification → post: 多对一(通知消息对应的post关系)
    post: Mapped["Post | None"] = relationship(back_populates="notifications")

    # notification → comment: 多对一(通知消息对应的comment关系)
    comment: Mapped["Comment | None"] = relationship(back_populates="notifications")
