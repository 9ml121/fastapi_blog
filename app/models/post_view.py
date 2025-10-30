"""
PostView 模型定义

记录用户浏览文章的历史，支持浏览量统计和浏览历史查询。

PostView 模型的关键设计决策：

  1. 不使用唯一约束（允许重复记录）：
    - 可以记录同一用户的多次浏览
    - 支持浏览次数统计和行为分析
    - 业务层控制防刷逻辑（is_duplicate方法）
  2. IP 和 User-Agent 可选：
    - 不是核心字段，设为可空
    - 隐私考虑：可以选择不记录
    - 分析需求：可以后续添加
  3. 级联删除策略：
    - 删除文章 → 删除所有浏览记录（CASCADE）
    - 删除用户 → 浏览记录变为匿名（CASCADE + NULL）
    - 符合数据生命周期管理
  4. 与 Post.view_count 的关系：
    - view_count：冗余字段，快速查询
    - PostView：详细记录，支持分析
    - 定期同步：确保数据一致性

"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class PostView(Base):
    """文章浏览记录模型

    记录用户浏览文章的历史，支持以下功能：
    1. 浏览量统计（Post.view_count）
    2. 用户浏览历史查询
    3. 热门文章分析（按浏览次数排序）
    4. 匿名用户浏览（user_id 可为 NULL）

    Attributes:
        id: 浏览记录唯一标识符
        user_id: 浏览用户ID（可空，支持匿名浏览）
        post_id: 被浏览的文章ID
        ip_address: 访问者IP地址（可选，用于防刷和分析）
        user_agent: 浏览器User-Agent（可选，用于设备分析）
        session_id: 会话标识符（可选，用于会话级别防刷）
        viewed_at: 浏览时间
        user: 浏览用户对象（关系）
        post: 被浏览的文章对象（关系）
    """

    __tablename__ = "post_views"

    # 复合索引：优化常见查询
    __table_args__ = (
        # 索引1：查询某篇文章的浏览记录（按时间倒序）
        Index("idx_post_viewed", "post_id", "viewed_at"),
        # 索引2：查询某用户的浏览历史（按时间倒序）
        Index("idx_user_viewed", "user_id", "viewed_at"),
        # 索引3：会话级别查询（用于防刷）
        Index("idx_session_viewed", "session_id", "viewed_at"),
        # 索引4：复合防刷查询（用户+文章+时间）
        Index("idx_user_post_time", "user_id", "post_id", "viewed_at"),
        # 索引5：会话防刷查询（会话+文章+时间）
        Index("idx_session_post_time", "session_id", "post_id", "viewed_at"),
        # 可选：如果需要去重（同一用户只记录一次浏览）
        # UniqueConstraint("user_id", "post_id", name="uq_user_post_view"),
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="浏览记录唯一标识符",
    )

    # 外键字段
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,  # 🔑 关键：允许 NULL
        index=True,
        comment="浏览用户ID（NULL表示匿名用户）",
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="被浏览的文章ID",
    )

    # 访问信息字段（用于防刷和数据分析）
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 最长 45 字符
        default=None,
        comment="访问者IP地址",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        default=None,
        comment="浏览器User-Agent信息",
    )

    session_id: Mapped[str | None] = mapped_column(
        String(32),  # 会话标识符长度
        default=None,
        index=True,
        comment="会话标识符（用于会话级别防刷）",
    )

    # 时间戳
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="浏览时间",
    )

    # 关系映射
    # PostView → User: 多对一（可选，支持匿名）
    user: Mapped[Optional["User"]] = relationship(
        back_populates="post_views",
        lazy="joined",  # 查询浏览记录时通常需要用户信息
    )

    # PostView → Post: 多对一(不指定 lazy策略，由应用层在需要时显式加载)
    post: Mapped["Post"] = relationship(
        back_populates="post_views",
    )

    # ============ 属性方法 ============

    @property
    def is_anonymous(self) -> bool:
        """判断是否为匿名浏览"""
        return self.user_id is None

    # ============ 业务方法 ============

    @staticmethod
    def is_duplicate_view(
        session,
        post_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        within_seconds: int = 86400,  # 默认一天（24小时）
    ) -> bool:
        """检查是否为重复浏览（增强防刷）

        防刷策略（按优先级）：
        1. 登录用户：只按 user_id 在时间窗口内防刷
        2. 匿名用户 + 会话ID：基于会话 + 时间窗口防刷
        3. 匿名用户 + IP地址：基于IP + 时间窗口防刷

        Args:
            session: 数据库会话
            post_id: 文章ID
            user_id: 用户ID（None表示匿名）
            session_id: 会话标识符（可选）
            ip_address: IP地址（可选）
            within_seconds: 时间窗口（秒），默认86400秒（24小时）

        Returns:
            bool: True表示重复浏览，False表示新浏览

        Example:
            >>> if not PostView.is_duplicate_view(session, post.id, user.id, session_id, ip_address):
            >>>     view = PostView(user_id=user.id, post_id=post.id, session_id=session_id)
            >>>     session.add(view)
        """  # noqa: E501
        from datetime import timedelta

        cutoff_time = datetime.now(UTC) - timedelta(seconds=within_seconds)

        # 策略1：登录用户，只按 user_id 判断
        if user_id:
            query = session.query(PostView).filter(
                PostView.post_id == post_id,
                PostView.user_id == user_id,
                PostView.viewed_at >= cutoff_time,
            )
            return query.first() is not None

        # 策略2：匿名用户 + 会话ID
        if session_id:
            query = session.query(PostView).filter(
                PostView.post_id == post_id,
                PostView.session_id == session_id,
                PostView.user_id.is_(None),
                PostView.viewed_at >= cutoff_time,
            )
            return query.first() is not None

        # 策略3：匿名用户 + IP地址
        if ip_address:
            query = session.query(PostView).filter(
                PostView.post_id == post_id,
                PostView.ip_address == ip_address,
                PostView.user_id.is_(None),
                PostView.viewed_at >= cutoff_time,
            )
            return query.first() is not None

        # 默认：不认为是重复浏览
        return False

    # ============ 特殊方法 ============

    def __repr__(self) -> str:
        """字符串表示"""
        user_info = f"user_id={self.user_id}" if self.user_id else "anonymous"
        return (
            f"<PostView(id={self.id}, {user_info}, post_id={self.post_id}, "
            f"viewed_at={self.viewed_at})>"
        )
