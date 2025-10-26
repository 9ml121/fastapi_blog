import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .post_favorite import PostFavorite
    from .post_like import PostLike
    from .post_view import PostView
    from .tag import Tag
    from .user import User


# 文章表和标签表多对多关系需要用到关联表
# 参考：https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many
# ⚠️ 直接用 Table 模型（没有业务属性），联合主键：(post_id, tag_id)，级联删除
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class PostStatus(str, Enum):
    """文章状态枚举"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档


class Post(Base):
    """posts数据库表模型

    设计要点：
    1. 使用 UUID 作为主键，支持分布式系统
    2. 支持草稿、发布、归档等完整状态管理
    3. 包含 SEO 友好的 slug 字段用于 URL
    4. 支持文章摘要（用于列表页展示）
    5. 包含置顶功能和浏览量统计
    6. 与 User，Comment, Tag 等模型建立关联关系
    """

    __tablename__ = "posts"

    @staticmethod
    def _generate_slug_from_title(title: str) -> str:
        """静态方法：从标题生成 URL 友好的 slug

        生成逻辑：
        1. 如果标题为空或 None，返回时间戳格式：文章-YYYYMMDD-HHMMSS
        2. 清理特殊字符，保留中文、英文、数字、空格、连字符
        3. 将空格转换为连字符，合并多个连字符
        4. 移除首尾连字符
        5. 长度超过 20 字符时智能截断
        6. 如果处理后为空，返回时间戳格式

        Args:
            title: 要生成 slug 的标题

        Returns:
            URL 友好的 slug 字符串

        Examples:
            >>> Post._generate_slug_from_title("如何学习FastAPI框架")
            "如何学习FastAPI框架"

            >>> Post._generate_slug_from_title("Python Web开发实战")
            "Python-Web开发实战"

            >>> Post._generate_slug_from_title("Vue3 + React对比分析!!!")
            "Vue3-React对比分析"

            >>> Post._generate_slug_from_title("")
            "文章-20251001-143022"  # 时间戳格式

            >>> Post._generate_slug_from_title("@#$%^&*()")
            "文章-20251001-143022"  # 全是特殊字符，返回时间戳
        """
        import re
        from datetime import datetime

        if not title:
            return f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # 基本清理：移除不友好的特殊字符
        cleaned = re.sub(r"[^\w\u4e00-\u9fff\s\-]", "", title)
        cleaned = re.sub(r"\s+", "-", cleaned.strip())
        cleaned = re.sub(r"-+", "-", cleaned)
        cleaned = cleaned.strip("-")

        # 长度控制
        if len(cleaned) > 20:
            truncated = cleaned[:17]
            if "-" in truncated[-10:]:
                last_dash = truncated.rfind("-")
                cleaned = truncated[:last_dash]
            else:
                cleaned = truncated + "..."

        return (
            cleaned
            if len(cleaned) >= 1
            else f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

    # 1. 主键
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, comment="文章唯一标识"
    )

    # 2. 核心业务字段 - 文章内容
    title: Mapped[str] = mapped_column(String(200), index=True, comment="文章标题")

    content: Mapped[str] = mapped_column(Text, comment="文章正文内容（Markdown 格式）")

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        comment="URL 友好标识（SEO 优化）",
    )

    summary: Mapped[str | None] = mapped_column(
        String(500), comment="文章摘要（用于列表页展示）"
    )

    # 3. 状态和配置字段

    # 配置字段
    is_featured: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="是否置顶文章"
    )

    # 状态字段
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus), default=PostStatus.DRAFT, index=True, comment="文章状态"
    )

    # 状态字段：浏览，点赞和收藏次数统计
    # ⚠️ alembic 迁移表新增字段时，需要手动设置 server_default=text("0")，
    # 否则会出现 NotNullViolation 错误
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览次数统计")

    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞次数统计")

    favorite_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="收藏次数统计"
    )

    # 4. 关联外键字段
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="作者用户 ID",
    )

    # 5. 时间戳字段
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        comment="发布时间（仅发布后设置）",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # 6. 关系定义
    # lazy 策略说明：
    # - "select"：默认值，按需查询，容易产生 N+1 问题
    # - "joined"：使用 LEFT JOIN，1次查询获取所有数据（推荐用于多对一关系）
    # - "selectin"：批量 IN 查询，适合一对多关系
    # - "subquery"：使用子查询，适合复杂场景

    # Post → User: 多对一（文章作者）
    # ⚠️ 这里Mapped["User"]必须要使用字符串（前向引用），避免循环导入
    author: Mapped["User"] = relationship(
        back_populates="posts",
        lazy="joined",  # 查询文章时通常需要作者信息
    )

    # Post → Comment: 一对多（文章所有评论列表）
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",  # 删除文章时，所有 comments都删除
        order_by="desc(Comment.created_at)",  # 按评论创建时间降序
    )

    # Post → Tag: 多对多（文章所有标签列表）
    tags: Mapped[list["Tag"]] = relationship(
        secondary="post_tags",  # ⚠️ 指定中间表为 post_tags
        back_populates="posts",
    )

    # Post → PostView: 一对多（文章所有浏览记录列表）
    post_views: Mapped[list["PostView"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",  # 删除文章时删除所有浏览记录
        order_by="desc(PostView.viewed_at)",  # 按浏览时间倒序
    )

    # Post → PostLike: 一对多（文章所有点赞记录列表）
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",  # 删除文章时删除所有点赞记录
        order_by="desc(PostLike.created_at)",  # 按点赞时间降序
    )

    # Post → PostFavorite: 一对多（文章所有收藏记录列表）
    favorites: Mapped[list["PostFavorite"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",  # 删除文章时删除所有收藏记录
        order_by="desc(PostFavorite.created_at)",  # 按收藏时间降序
    )

    def __repr__(self) -> str:
        """开发调试用的字符串表示"""
        return (
            f"<Post(id={self.id}, title='{self.title[:30]}...', "
            f"status='{self.status}')>"
        )

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return self.display_title

    # 业务状态检查属性
    @property
    def is_draft(self) -> bool:
        """检查是否为草稿状态"""
        return self.status == PostStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """检查是否已发布"""
        return self.status == PostStatus.PUBLISHED

    @property
    def is_archived(self) -> bool:
        """检查是否已归档"""
        return self.status == PostStatus.ARCHIVED

    @property
    def display_title(self) -> str:
        """显示标题（带状态标识）"""
        status_map = {
            PostStatus.DRAFT: "[草稿] ",
            PostStatus.ARCHIVED: "[归档] ",
            PostStatus.PUBLISHED: "",
        }
        prefix = status_map.get(self.status, "")
        return f"{prefix}{self.title}"

    @property
    def word_count(self) -> int:
        """估算文章字数（简单实现）"""
        if not self.content:
            return 0
        # 简单的字数统计（可根据需要优化）
        return len(self.content.replace(" ", "").replace("\n", ""))

    @property
    def reading_time(self) -> int:
        """估算阅读时间（分钟）"""
        # 假设平均阅读速度 200 字/分钟
        return max(1, self.word_count // 200)

    # 业务操作方法
    def publish(self) -> None:
        """发布文章"""
        self.status = PostStatus.PUBLISHED
        if not self.published_at:
            self.published_at = datetime.now()

    def archive(self) -> None:
        """归档文章"""
        self.status = PostStatus.ARCHIVED

    def revert_to_draft(self) -> None:
        """恢复为草稿状态"""
        self.status = PostStatus.DRAFT
        self.published_at = None

    def toggle_featured(self) -> None:
        """切换置顶状态"""
        self.is_featured = not self.is_featured

    def increment_view_count(self) -> None:
        """增加浏览次数"""
        self.view_count += 1

    def increment_like_count(self) -> None:
        """增加点赞数"""
        self.like_count += 1

    def decrement_like_count(self) -> None:
        """减少点赞数（防止负数）"""
        if self.like_count > 0:
            self.like_count -= 1

    def increment_favorite_count(self) -> None:
        """增加收藏数"""
        self.favorite_count += 1

    def decrement_favorite_count(self) -> None:
        """减少收藏数（防止负数）"""
        if self.favorite_count > 0:
            self.favorite_count -= 1

    def set_summary_from_content(self, max_length: int = 100) -> None:
        """从文章内容自动生成摘要

        Args:
            max_length: 摘要最大长度，默认 100 字符
        """
        if not self.content:
            self.summary = None
            return

        # 移除 Markdown 格式标记的简单实现
        import re

        clean_content = re.sub(r"[#*`\[\]()]", "", self.content)
        clean_content = re.sub(r"\s+", " ", clean_content.strip())

        if len(clean_content) <= max_length:
            self.summary = clean_content
        else:
            # 在合适的位置截断，避免截断单词
            truncated = clean_content[:max_length]
            last_space = truncated.rfind(" ")
            if last_space > max_length * 0.8:  # 如果最后一个空格位置合理
                self.summary = truncated[:last_space] + "..."
            else:
                self.summary = truncated + "..."
