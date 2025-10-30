"""
Follow CRUD 操作

提供“关注/取消关注/查询粉丝与关注列表/关注状态/粉丝数量”等核心功能，服务后续通知和社交互动。
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidParametersError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.pagination import PaginationParams, paginate_query
from app.crud import user as user_crud
from app.crud.notification import NotificationEvent, emit_notification_event
from app.models.follow import Follow
from app.models.user import User
from app.schemas.follow import FollowUserSummary


def _ensure_user_exists(
    db: Session,
    user_id: UUID,
    *,
    resource: str = "用户",
) -> User:
    """确认给定用户存在，否则抛出 404 异常。"""

    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise ResourceNotFoundError(resource=resource)
    return user


def follow_user(db: Session, follower_id: UUID, followed_id: UUID) -> Follow:
    """关注用户

    设计要点：防止自我关注；防止重复关注；自动创建 Follow 记录

    Args:
        db: 数据库会话
        follower_id: 关注者ID
        followed_id: 被关注者ID

    Returns:
        Follow: 关注关系
    """
    # 1. 检查被关注的用户是否存在 404
    _ensure_user_exists(db, followed_id, resource="被关注的用户")

    # 2. 检查自我关注 400
    if follower_id == followed_id:
        raise InvalidParametersError(message="不能关注自己")

    # 3. 检查是否已关注 409
    if is_following(db=db, follower_id=follower_id, followed_id=followed_id):
        raise ResourceConflictError(message="已经关注过该用户")

    # 4. 创建关注关系
    follow = Follow(follower_id=follower_id, followed_id=followed_id)
    db.add(follow)  # 添加到会话

    # 5. 触发通知：仅在关注者与被关注者不同的情况下
    emit_notification_event(
        db=db,
        event_type=NotificationEvent.USER_FOLLOWED,
        recipient_id=followed_id,
        actor_id=follower_id,
    )

    db.commit()  # 提交事务
    db.refresh(follow)  # 刷新对象
    return follow


def unfollow_user(db: Session, follower_id: UUID, followed_id: UUID) -> bool:
    """取消关注用户

    设计要点：查找记录并删除；没有即抛出 ResourceNotFoundError

    Args:
        db: 数据库会话
        follower_id: 关注者ID
        followed_id: 被关注者ID

    Returns:
        bool: 是否取消关注
    """
    # 0. 检查被关注的用户是否存在
    _ensure_user_exists(db, followed_id, resource="被关注的用户")

    # 1. 查找记录
    follow = (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.followed_id == followed_id)
        .first()
    )

    if not follow:
        raise ResourceNotFoundError(resource="关注关系")

    # 2. 删除记录
    db.delete(follow)  # 删除记录
    db.commit()  # 提交事务
    return True  # 返回 True 表示取消关注成功


def is_following(db: Session, follower_id: UUID, followed_id: UUID) -> bool:
    """检查是否关注

    设计要点：快速布尔判断；可用于接口返回状态

    Args:
        db: 数据库会话
        follower_id: 关注者ID
        followed_id: 被关注者ID

    Returns:
        bool: 是否关注
    """
    # 1. 检查被关注的用户是否存在 404
    _ensure_user_exists(db, followed_id, resource="被关注的用户")

    return (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.followed_id == followed_id)
        .first()
        is not None
    )


def get_followers(
    db: Session,
    user_id: UUID,
    pagination_params: PaginationParams,
    *,
    viewer_id: UUID | None = None,
) -> tuple[list[FollowUserSummary], int]:
    """获取粉丝列表(分页)

    Args:
        db: 数据库会话
        user_id: 用户ID
        pagination_params: 分页参数

    Returns:
        tuple[list[User], int]: 粉丝列表和总记录数
    """
    _ensure_user_exists(db, user_id, resource="用户")

    query = (
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followed_id == user_id)
    )

    users, total = paginate_query(
        db=db, query=query, params=pagination_params, model=User
    )

    if not users:
        return [], total

    followed_ids: set[UUID] | None = None
    if viewer_id:
        followed_ids = set(
            db.scalars(
                select(Follow.followed_id)
                .where(Follow.follower_id == viewer_id)
                .where(Follow.followed_id.in_([user.id for user in users]))
            )
        )  # type: ignore

    rows = _build_follow_user_summary_list(users, followed_ids)

    return rows, total


def get_following(
    db: Session,
    user_id: UUID,
    pagination_params: PaginationParams,
    *,
    viewer_id: UUID | None = None,
) -> tuple[list[FollowUserSummary], int]:
    """获取关注列表(分页)

    使用场景：
    1. 快速查询用户关注列表；
    2. 在查询到的用户关注列表中，找出当前登录用户（由 viewer_id 代表）已经关注了哪些人。

    Args:
        db: 数据库会话
        user_id: 用户ID
        pagination_params: 分页参数

    Returns:
        tuple[list[FollowUserSummary], int]: 关注列表和总记录数
    """
    _ensure_user_exists(db, user_id, resource="用户")

    # 1. 查询用户关注列表
    query = (
        select(User)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == user_id)
    )

    # 2. 执行分页逻辑
    users, total = paginate_query(
        db=db, query=query, params=pagination_params, model=User
    )

    if not users:
        return [], total

    # 3. 找出当前登录用户已经关注了哪些人
    followed_ids: set[UUID] | None = None
    if viewer_id:
        followed_ids = set(
            db.scalars(
                select(Follow.followed_id)
                .where(Follow.follower_id == viewer_id)
                .where(Follow.followed_id.in_([user.id for user in users]))
            )
        )  # type: ignore

    # 4. 构建 FollowUserSummary 列表
    rows = _build_follow_user_summary_list(users, followed_ids)

    # 5. 返回结果
    return rows, total


def get_follower_count(db: Session, user_id: UUID) -> int:
    """获取粉丝数

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        int: 粉丝数
    """
    _ensure_user_exists(db, user_id, resource="用户")

    return db.query(Follow).filter(Follow.followed_id == user_id).count()


def _build_follow_user_summary_list(
    users: list[User], followed_ids: set[UUID] | None
) -> list[FollowUserSummary]:
    """根据用户列表构建 FollowUserSummary 数据"""

    if not followed_ids:
        return [
            FollowUserSummary(
                id=user.id,
                username=user.username,
                nickname=user.nickname,
                avatar=user.avatar,
                bio=user.bio,
                is_following=False,
            )
            for user in users
        ]

    return [
        FollowUserSummary(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            bio=user.bio,
            is_following=user.id in followed_ids,
        )
        for user in users
    ]
