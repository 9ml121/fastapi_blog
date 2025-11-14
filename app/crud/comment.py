"""
app/crud/comment.py

评论相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.crud.post as post_crud
from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.pagination import PaginatedResponse, PaginationParams, paginate_query
from app.crud.notification import NotificationEvent, emit_notification_event
from app.crud.user import get_user_by_id
from app.models.comment import Comment
from app.schemas.comment import CommentCreate


# ================ 查询方法 ================
def get_comment_by_id(db: Session, comment_id: UUID) -> Comment | None:
    """获取评论详情

    Args:
        db: 数据库会话
        comment_id: 评论ID

    Returns:
        Comment: 评论对象
    """
    return db.get(Comment, comment_id)


def get_comment_by_post_id(
    db: Session, post_id: UUID, params: PaginationParams
) -> PaginatedResponse[Comment]:
    """获取文章的所有顶级评论（树形结构）

    Args:
        db: 数据库会话
        post_id: 文章ID
        params: 分页参数。默认page=1, size=20, sort=created_at, order=desc

    Returns:
        PaginatedResponse[Comment]: 分页响应
    """
    # 业务规则：文章必须存在才能查询评论
    post = post_crud.get_post_by_id(db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 构建查询
    query = select(Comment).where(
        Comment.post_id == post_id, Comment.parent_id.is_(None)
    )

    # 执行分页
    items, total = paginate_query(db, query, params, model=Comment)

    # 返回分页响应 (FastAPI 会自动序列化 SQLAlchemy 模型)
    return PaginatedResponse.create(items, total, params)


# ================ 创建方法 ================
def create_comment(
    db: Session, obj_in: CommentCreate, author_id: UUID, post_id: UUID
) -> Comment:
    """创建评论

    Args:
        db: 数据库会话
        obj_in: 评论创建数据
        author_id: 评论作者ID
        post_id: 文章ID

    Returns:
        Comment: 评论对象
    """
    # 1. 验证文章存在
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 如果是回复评论，验证父评论存在且属于该文章
    parent_comment: Comment | None = None
    if obj_in.parent_id:
        parent_comment = get_comment_by_id(db, comment_id=obj_in.parent_id)
        if not parent_comment:
            raise ResourceNotFoundError(resource="父评论")

        # 验证父评论属于同一文章（防止跨文章回复）
        if parent_comment.post_id != post_id:
            raise ResourceConflictError(message="父评论不属于该文章")

    # 3. 创建评论
    comment = Comment(
        content=obj_in.content,
        user_id=author_id,
        post_id=post_id,
        parent_id=obj_in.parent_id,
    )
    db.add(comment)
    db.flush()

    # 4.1 通知文章作者（文章评论，不传 comment_id 以实现基于文章的聚合）
    emit_notification_event(
        db=db,
        event_type=NotificationEvent.POST_COMMENTED,
        recipient_id=post.author_id,
        actor_id=author_id,
        post_id=post_id,
        comment_id=None,  # 文章评论设为 None，实现基于文章的聚合
    )

    # 4.2 如果是回复评论，通知父评论作者（评论回复，基于父评论 ID 聚合）
    if parent_comment and parent_comment.user_id not in {post.author_id, author_id}:
        emit_notification_event(
            db=db,
            event_type=NotificationEvent.COMMENT_REPLIED,
            recipient_id=parent_comment.user_id,
            actor_id=author_id,
            post_id=post_id,
            comment_id=parent_comment.id,  # 使用父评论 ID 实现基于评论的聚合
        )

    db.commit()
    db.refresh(comment)

    return comment


# ================ 删除方法 ================
def delete_comment(
    db: Session, *, comment_id: UUID, post_id: UUID, user_id: UUID
) -> None:
    """删除评论

    Args:
        db: 数据库会话
        comment_id: 评论ID
        post_id: 文章ID
        user_id: 删除评论的用户ID

    Returns:
        bool: 是否删除成功
    """
    # 1. 验证评论存在
    comment = get_comment_by_id(db, comment_id=comment_id)
    if not comment:
        raise ResourceNotFoundError(resource="评论")

    # 2. 验证评论属于该文章
    if comment.post_id != post_id:
        raise ResourceConflictError(message="评论不属于该文章")

    # 3. 权限检查：只有评论作者或者管理员可以删除
    user = get_user_by_id(db=db, user_id=user_id)
    if comment.user_id != user_id and user and not user.is_admin:
        raise PermissionDeniedError(message="无权删除他人评论")

    # 4. 删除评论
    db.delete(comment)
    db.commit()

    return None
