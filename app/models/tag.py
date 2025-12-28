import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .post import Post


class Tag(Base):
    """tags数据库表模型

    用于文章分类和标记，支持与文章的多对多关系。

    Attributes:
        id: 标签唯一标识符
        name: 标签名称（唯一）
        slug: URL 友好的标识符（唯一）
        description: 标签描述（可选）
        created_at: 创建时间
        updated_at: 更新时间
        posts: 使用此标签的文章列表（多对多关系）
    """

    __tablename__ = "tags"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="标签唯一标识符",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        comment="标签名称（唯一）",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="URL 友好的标识符",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        default=None,
        comment="标签描述",
    )

    # 时间戳
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

    # 关系映射：多对多关系（Tag ↔ Post）
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        secondary="post_tags",  # 通过中间表关联
        back_populates="tags",
        lazy="selectin",  # 避免 N+1 查询
        doc="使用此标签的文章列表",
    )

    # ============ 计算属性 ============

    @property
    def post_count(self) -> int:
        """返回使用此标签的文章数量"""
        return len(self.posts)

    # ============ 业务方法 ============

    @staticmethod
    def normalize_name(name: str) -> str:
        """标准化标签名称

        规则：
        1. 去除首尾空格
        2. 将内部多个空格替换为单个空格
        3. 首字母大写（可选，根据业务需求）

        Args:
            name: 原始标签名称

        Returns:
            标准化后的标签名称

        Example:
            >>> Tag.normalize_name("  python   programming  ")
            "Python programming"
        """
        # 去除首尾空格，将内部多个空格替换为单个
        normalized = " ".join(name.strip().split())
        # 首字母大写（可根据业务调整）
        return normalized.capitalize()

    @staticmethod
    def generate_slug(name: str) -> str:
        """从标签名称生成 URL 友好的 slug

        规则：
        1. 转换为小写
        2. 将空格替换为连字符
        3. 只保留字母、数字、连字符

        Args:
            name: 标签名称

        Returns:
            URL 友好的 slug

        Example:
            >>> Tag.generate_slug("Python Programming")
            "python-programming"
        """
        import re

        # 转小写
        slug = name.lower()
        # 将空格替换为连字符
        slug = slug.replace(" ", "-")
        # 只保留字母、数字、连字符、中文（明确指定范围）
        slug = re.sub(r"[^a-zA-Z0-9\-\u4e00-\u9fff]", "", slug)
        # 将多个连字符替换为单个
        slug = re.sub(r"-+", "-", slug)
        # 去除首尾连字符
        slug = slug.strip("-")

        return slug

    # ============ 特殊方法 ============

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<Tag(id={self.id}, name='{self.name}', slug='{self.slug}', "
            f"post_count={self.post_count})>"
        )
