"""
app/crud/comment.py

评论相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.pagination import PaginationParams, paginate_query
from app.crud.base import CRUDBase
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate


class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    """评论 CRUD 操作类

    提供评论的创建、查询、更新、删除等操作。
    """

    def create_with_author(
        self,
        db: Session,
        *,
        obj_in: CommentCreate,
        author_id: UUID,
        post_id: UUID,
    ) -> Comment:
        """创建评论（关联作者和文章）

        与 CRUDBase.create() 的区别：
        - 自动设置 author_id 和 post_id
        - 封装业务逻辑，避免 API 层手动设置关联

        Args:
            db: 数据库会话。
            obj_in: 评论创建数据（content, parent_id）。
            author_id: 评论作者的用户 ID。
            post_id: 所属文章的 ID。

        Returns:
            创建成功的评论对象。

        示例:
            >>> comment = crud.comment.create_with_author(
            ...     db,
            ...     obj_in=CommentCreate(content="很棒的文章！"),
            ...     author_id=user.id,
            ...     post_id=post.id,
            ... )
        """
        # 使用 CRUDBase.create() 的 **kwargs 功能传入额外字段
        comment = self.create(
            db,
            obj_in=obj_in,
            user_id=author_id,  # 设置作者 ID
            post_id=post_id,  # 设置文章 ID
        )
        return comment

    def get_by_post(
        self,
        db: Session,
        *,
        post_id: UUID,
    ) -> list[Comment]:
        """获取文章的所有顶级评论（树形结构）

        设计要点：
        1. 只返回顶级评论（parent_id=None）
        2. 子评论通过 Comment.replies 关系自动加载（lazy="selectin"）
        3. 按创建时间倒序排列（最新评论在前）

        性能优化：
        - 使用 lazy="selectin" 避免 N+1 查询
        - 总查询次数：2 次（1 次顶级评论 + 1 次所有子评论）

        Args:
            db: 数据库会话。
            post_id: 文章 ID。

        Returns:
            顶级评论列表，每个评论递归包含 replies 子评论。

        示例:
            >>> comments = crud.comment.get_by_post(db, post_id=post.id)
            >>> # 返回：[Comment(replies=[Comment(), Comment()]), Comment(replies=[])]
        """
        # SQLAlchemy 传统语法（Legacy）
        return (
            db.query(Comment)
            .filter(
                Comment.post_id == post_id,  # 条件1：属于该文章
                Comment.parent_id.is_(None),  # 条件2：顶级评论
            )
            .order_by(Comment.created_at.desc())  # 最新评论在前
            .all()
        )

    def get_paginated_by_post(
        self,
        db: Session,
        *,
        post_id: UUID,
        params: PaginationParams,
    ) -> tuple[list[Comment], int]:
        """获取文章的分页评论列表

        使用新的分页工具，支持：
        - 分页：page/size 参数
        - 排序：sort/order 参数（默认按 created_at desc）
        - 安全验证：自动验证排序字段
        - 只返回顶级评论（parent_id=None），子评论通过 replies 字段递归获取

        Args:
            db: 数据库会话
            post_id: 文章ID
            params: 分页参数

        Returns:
            tuple: (顶级评论列表, 总记录数)
        """
        # SQLAlchemy 现代语法（Modern）构建查询
        query = select(Comment)

        # 添加过滤条件：post_id 和 parent_id.is_(None)
        query = query.where(Comment.post_id == post_id, Comment.parent_id.is_(None))

        # 调用分页工具执行查询
        items, total = paginate_query(db, query, params, model=Comment)

        return items, total


# 创建单例实例
comment = CRUDComment(Comment)
