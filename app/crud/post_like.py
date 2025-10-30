from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidParametersError, ResourceNotFoundError
from app.crud.notification import NotificationEvent, emit_notification_event
from app.crud.post import get_post_by_id
from app.crud.user import get_user_by_id
from app.models.post import Post, PostStatus
from app.models.post_like import PostLike
from app.models.user import User


def toggle_like(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """点赞/取消点赞（幂等，含事件触发）

    Args:
        db (Session): 数据库会话
        user_id (UUID): 用户ID
        post_id (UUID): 文章ID

    Returns:
        bool: 是否点赞成功，True 表示点赞成功，False 表示取消点赞成功
    """
    # 1. 校验文章存在和状态
    post = db.get(Post, post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    if post.status != PostStatus.PUBLISHED:
        raise InvalidParametersError(message="只能对已发布文章进行互动操作")

    # 2. 查询当前状态
    existing_like = (
        db.query(PostLike).filter_by(user_id=user_id, post_id=post_id).first()
    )

    if existing_like:
        # 3. 取消点赞
        db.delete(existing_like)
        # post.decrement_like_count()
        # 使用原子操作递减 like_count，防止并发问题
        db.query(Post).filter(Post.id == post_id, Post.like_count > 0).update(
            {Post.like_count: Post.like_count - 1}, synchronize_session=False
        )
        # db.query(Post)查询后在修改 post属性，就不需要 db.add(post),可以直接提交
        db.commit()
        return False
    else:
        # 4. 添加点赞
        new_like = PostLike(user_id=user_id, post_id=post_id)
        db.add(new_like)

        # 使用原子操作递增 like_count，防止并发问题
        db.query(Post).filter(Post.id == post_id).update(
            {Post.like_count: Post.like_count + 1}, synchronize_session=False
        )

        # 5. 触发通知：仅在作者与点赞用户不同的情况下
        emit_notification_event(
            db=db,
            event_type=NotificationEvent.POST_LIKED,
            recipient_id=post.author_id,
            actor_id=user_id,
            post_id=post_id,
        )
        db.commit()
        return True


def is_liked(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """检查用户是否已点赞文章

    Args:
        db (Session): 数据库会话
        user_id (UUID): 用户ID
        post_id (UUID): 文章ID

    Returns:
        bool: 是否点赞，True 表示已点赞，False 表示未点赞
    """
    like_record = db.query(PostLike).filter_by(user_id=user_id, post_id=post_id).first()

    return like_record is not None


def get_user_liked_post_ids(
    db: Session, user_id: UUID, post_ids: list[UUID] | None = None
) -> set[UUID]:
    """获取用户点赞的文章ID集合（批量检查）

    Args:
        db: 数据库会话
        user_id: 用户ID
        post_ids: 要检查的文章ID列表（可选）

    Returns:
        set[UUID]: 已点赞的文章ID集合

    用途：
    - 前端列表页显示点赞状态
    - 批量检查多篇文章的点赞状态
    """
    query = db.query(PostLike.post_id).filter(PostLike.user_id == user_id)

    if post_ids:
        query = query.filter(PostLike.post_id.in_(post_ids))

    return {post_id for (post_id,) in query.all()}


def get_user_liked_posts(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 20
) -> list[Post]:
    """获取用户点赞的文章列表

    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过记录数（分页）
        limit: 限制记录数（分页）

    Returns:
        list[Post]: 用户点赞的文章列表
    """
    # 验证用户存在
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise ResourceNotFoundError(resource="用户")

    return (
        db.query(Post)
        .join(PostLike)
        .filter(PostLike.user_id == user_id)
        .order_by(PostLike.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_post_liked_users(
    db: Session, post_id: UUID, skip: int = 0, limit: int = 20
) -> list[User]:
    """获取文章点赞的用户列表

    Args:
        db: 数据库会话
        post_id: 文章ID
        skip: 跳过记录数（分页）
        limit: 限制记录数（分页）

    Returns:
        list[User]: 点赞文章的用户列表
    """
    # 验证文章存在
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    return (
        db.query(User)
        .join(PostLike)
        .filter(PostLike.post_id == post_id)
        .order_by(PostLike.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
