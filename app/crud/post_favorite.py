from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidParametersError, ResourceNotFoundError
from app.crud.post import get_post_by_id
from app.crud.user import get_user_by_id
from app.models.post import Post, PostStatus
from app.models.post_favorite import PostFavorite
from app.models.user import User


def toggle_favorite(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """切换收藏状态（幂等）

    Args:
        db: 数据库会话
        user_id: 用户ID
        post_id: 文章ID

    Returns:
        bool: True=收藏成功, False=取消收藏成功

    Raises:
        ResourceNotFoundError: 文章不存在
        InvalidParametersError: 文章未发布
    """
    # 1. 校验文章存在和状态
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    if post.status != PostStatus.PUBLISHED:
        raise InvalidParametersError(message="只能对已发布文章进行收藏操作")

    # 2. 查询当前收藏状态
    existing_favorite = (
        db.query(PostFavorite).filter_by(user_id=user_id, post_id=post_id).first()
    )

    if existing_favorite:
        # 3. 取消收藏
        db.delete(existing_favorite)
        post.decrement_favorite_count()
        db.commit()
        return False
    else:
        # 4. 添加收藏
        new_favorite = PostFavorite(user_id=user_id, post_id=post_id)
        db.add(new_favorite)
        post.increment_favorite_count()
        db.commit()
        return True


def is_favorited(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """检查用户是否已收藏文章

    Args:
        db: 数据库会话
        user_id: 用户ID
        post_id: 文章ID

    Returns:
        bool: True=已收藏, False=未收藏
    """
    favorite_record = (
        db.query(PostFavorite).filter_by(user_id=user_id, post_id=post_id).first()
    )
    return favorite_record is not None


def get_user_favorited_post_ids(
    db: Session, user_id: UUID, post_ids: list[UUID] | None = None
) -> set[UUID]:
    """获取用户收藏的文章ID集合（批量检查）

    Args:
        db: 数据库会话
        user_id: 用户ID
        post_ids: 要检查的文章ID列表（可选）

    Returns:
        set[UUID]: 已收藏的文章ID集合

    用途：
    - 前端列表页显示收藏状态
    - 批量检查多篇文章的收藏状态
    """
    query = db.query(PostFavorite.post_id).filter(PostFavorite.user_id == user_id)

    if post_ids:
        query = query.filter(PostFavorite.post_id.in_(post_ids))

    return {post_id for (post_id,) in query.all()}


def get_user_favorited_posts(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 20
) -> list[Post]:
    """获取用户收藏的文章列表

    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过记录数（分页）
        limit: 限制记录数（分页）


    Returns:
        list[Post]: 用户收藏的文章列表
    """
    # 验证用户存在
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise ResourceNotFoundError(resource="用户")

    return (
        db.query(Post)
        .join(PostFavorite)
        .filter(PostFavorite.user_id == user_id)
        .order_by(PostFavorite.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_post_favorited_users(
    db: Session, post_id: UUID, skip: int = 0, limit: int = 20
) -> list[User]:
    """获取文章收藏的用户列表

    Args:
        db: 数据库会话
        post_id: 文章ID
        skip: 跳过记录数（分页）
        limit: 限制记录数（分页）

    Returns:
        list[User]: 收藏文章的用户列表
    """
    # 验证文章存在
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    return (
        db.query(User)
        .join(PostFavorite)
        .filter(PostFavorite.post_id == post_id)
        .order_by(PostFavorite.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
