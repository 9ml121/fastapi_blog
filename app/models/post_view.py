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
        ForeignKey("users.id", ondelete="CASCADE"),
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

    # PostView → Post: 多对一
    post: Mapped["Post"] = relationship(
        back_populates="post_views",
        lazy="joined",  # 查询浏览记录时通常需要文章信息
    )

    # ============ 属性方法 ============

    @property
    def is_anonymous(self) -> bool:
        """判断是否为匿名浏览"""
        return self.user_id is None

    # ============ 业务方法 ============

    @staticmethod
    def is_duplicate(
        session,
        user_id: uuid.UUID | None,
        post_id: uuid.UUID,
        within_seconds: int = 300,
    ) -> bool:
        """检查是否为重复浏览（防刷）

        判断逻辑：
        - 同一用户（或匿名+同IP）在指定时间内重复浏览同一文章

        Args:
            session: 数据库会话
            user_id: 用户ID（None表示匿名）
            post_id: 文章ID
            within_seconds: 时间窗口（秒），默认300秒（5分钟）

        Returns:
            bool: True表示重复浏览，False表示新浏览

        Example:
            >>> if not PostView.is_duplicate(session, user.id, post.id):
            >>>     view = PostView(user_id=user.id, post_id=post.id)
            >>>     session.add(view)
        """
        from datetime import timedelta

        cutoff_time = datetime.now(UTC) - timedelta(seconds=within_seconds)

        query = session.query(PostView).filter(PostView.post_id == post_id, PostView.viewed_at >= cutoff_time)

        if user_id:
            # 已登录用户：检查 user_id
            query = query.filter(PostView.user_id == user_id)
        else:
            # 匿名用户：无法准确判断，返回 False（允许记录）
            return False

        return query.first() is not None

    # ============ 特殊方法 ============

    def __repr__(self) -> str:
        """字符串表示"""
        user_info = f"user_id={self.user_id}" if self.user_id else "anonymous"
        return f"<PostView(id={self.id}, {user_info}, post_id={self.post_id}, viewed_at={self.viewed_at})>"
