"""
app/crud/comment.py

评论相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

import app.crud.post as post_crud
from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.crud.base import CRUDBase
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate


class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    """评论 CRUD 操作类

    提供评论的创建、查询、更新、删除等操作。
    """

    def create_comment(
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
        - 验证文章和父评论存在且属于该文章

        Args:
            db: 数据库会话。
            obj_in: 评论创建数据（content, parent_id）。
            author_id: 评论作者的用户 ID。
            post_id: 所属文章的 ID。

        Returns:
            201: 创建成功的评论对象。
            404: 文章不存在
            404: 父评论不存在
            409: 父评论不属于该文章

        示例:
            >>> comment = crud.comment.create_comment(
            ...     db,
            ...     obj_in=CommentCreate(content="很棒的文章！"),
            ...     author_id=user.id,
            ...     post_id=post.id,
            ... )
        """
        # 1. 验证文章存在
        post = post_crud.get_post_by_id(db=db, post_id=post_id)
        if not post:
            raise ResourceNotFoundError(resource="文章")

        # 2. 如果是回复评论，验证父评论存在且属于该文章
        if obj_in.parent_id:
            parent_comment = self.get(db, id=obj_in.parent_id)
            if not parent_comment:
                raise ResourceNotFoundError(resource="父评论")

            # 验证父评论属于同一文章（防止跨文章回复）
            if parent_comment.post_id != post_id:
                raise ResourceConflictError(message="父评论不属于该文章")

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

        ⚠️ 过时方法，请使用 build_top_level_comments_query 代替

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

    def build_top_level_comments_query(
        self,
        db: Session,
        *,
        post_id: UUID,
    ) -> Select[tuple[Comment]]:
        """构建顶级评论的查询对象，包含业务规则验证

        Args:
            db: 数据库会话。
            post_id: 文章ID

        Returns:
            Select[tuple[Comment]]: SQLAlchemy 查询对象（未执行）
        """
        # 业务规则：文章必须存在才能查询评论
        post = post_crud.get_post_by_id(db, post_id=post_id)
        if not post:
            raise ResourceNotFoundError(resource="文章")

        # SQLAlchemy 现代语法（Modern）构建查询
        query = select(Comment)

        # 添加过滤条件：post_id 和 parent_id.is_(None)
        query = query.where(Comment.post_id == post_id, Comment.parent_id.is_(None))

        return query


# 创建单例实例
comment = CRUDComment(Comment)
