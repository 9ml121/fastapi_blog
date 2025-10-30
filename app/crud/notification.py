"""Notification CRUD 操作

支持高频事件的通知创建、聚合、查询、已读管理等基础操作，
为后续 API + 事件驱动提供数据层支持。
"""

from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ResourceNotFoundError
from app.core.pagination import PaginationParams, paginate_query
from app.core.time_utils import ensure_utc, utc_now
from app.models.notification import Notification, NotificationType
from app.models.post import Post


class NotificationEvent(str, Enum):
    """业务事件类型（采用事件驱动架构）"""

    POST_LIKED = "post_liked"  # 文章被点赞
    POST_COMMENTED = "post_commented"  # 文章被评论
    COMMENT_REPLIED = "comment_replied"  # 评论被回复
    USER_FOLLOWED = "user_followed"  # 用户被关注
    # 后续可扩展：POST_MENTIONED、COMMENT_MENTIONED 等


def emit_notification_event(
    db: Session,
    event_type: NotificationEvent,
    recipient_id: UUID,
    actor_id: UUID,
    post_id: UUID | None = None,
    comment_id: UUID | None = None,
) -> Notification | None:
    """通知系统统一事件入口

    - 对业务层暴露的唯一入口，负责协调事件到通知的转换
    - 预留扩展点：事件过滤、异步派发、偏好设置等

    Args:
        db: 数据库会话
        event_type: 业务事件类型
        recipient_id: 通知接收人ID
        actor_id: 操作发起人ID
        post_id: 关联文章ID
        comment_id: 关联评论ID

    Returns:
        Notification | None: 创建或聚合后的通知；如果无需创建则返回 None
    """

    # 防御性校验：不通知自己
    if recipient_id == actor_id:
        return None

    # 映射事件类型到通知类型
    # 未来可在此处加入用户偏好、黑名单、速率限制等逻辑
    event_to_notification_type = {
        NotificationEvent.POST_LIKED: NotificationType.LIKE,
        NotificationEvent.POST_COMMENTED: NotificationType.COMMENT,
        NotificationEvent.COMMENT_REPLIED: NotificationType.COMMENT,
        NotificationEvent.USER_FOLLOWED: NotificationType.FOLLOW,
    }

    notification_type = event_to_notification_type.get(event_type)

    if not notification_type:
        # 未知事件暂时忽略，可在此记录日志或抛出异常
        return None

    # 调用聚合创建函数
    return create_or_update_notification(
        db=db,
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
        comment_id=comment_id,
    )


def _should_aggregate_notification(
    existing_notification: Notification,
    notification_type: NotificationType,
) -> bool:
    """判断是否应该聚合到现有通知

    触发聚合的条件（更新）：
    1. 通知类型相同（LIKE, COMMENT, FOLLOW）
    2. 资源相同（post_id 或 recipient_id for FOLLOW）
    3. 时间在聚合窗口内：
       - 点赞/评论：1 小时
       - 关注：24 小时

    Args:
        existing_notification: 现有通知
        notification_type: 通知类型

    Returns:
        bool: 是否应该聚合
    """
    # 不同类型使用不同的聚合窗口
    aggregation_windows = {
        NotificationType.LIKE: 3600,  # 1小时
        NotificationType.COMMENT: 3600,  # 1小时
        NotificationType.FOLLOW: 86400,  # 24小时
    }

    aggregation_window = aggregation_windows.get(notification_type, 3600)
    # 确保都是 aware datetime
    last_updated = ensure_utc(existing_notification.last_updated_at)
    time_diff = (utc_now() - last_updated).total_seconds()

    return time_diff < aggregation_window


def create_or_update_notification(
    db: Session,
    recipient_id: UUID,
    actor_id: UUID,
    notification_type: NotificationType,
    post_id: UUID | None = None,
    comment_id: UUID | None = None,
) -> Notification:
    """创建或更新通知，支持聚合（⚠️注意没有 commit，让调用者来决定何时 commit）


    聚合策略：
    1. POST_COMMENTED（文章评论）：
      基于 (recipient_id, post_id, notification_type) 聚合，
      忽略 comment_id，因为用户关心的是"文章被评论了"，而不是"哪个具体评论"

    2. COMMENT_REPLIED（评论回复）：
      基于 (recipient_id, comment_id, notification_type) 聚合，
      保留 comment_id，因为用户关心的是"我的评论被回复了"

    3. LIKE（点赞）：
      基于 (recipient_id, post_id, notification_type) 聚合，

    4. FOLLOW（关注）：
      基于 (recipient_id, notification_type) 聚合，


    Args:
        db: 数据库会话
        recipient_id: 通知接收人ID
        actor_id: 操作发起人ID
        notification_type: 通知类型
        post_id: 文章ID，FOLLOW 时为 None
        comment_id: 评论ID，LIKE 和 POST_COMMENTED 时为 None

    Returns:
        Notification: 通知对象
    """
    # Step 1: 构建基础查询条件
    base_query = db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.notification_type == notification_type,
    )

    existing_notification = None

    # Step 2: 根据通知类型决定聚合粒度
    if notification_type == NotificationType.LIKE:
        # 点赞通知：基于 (recipient_id, post_id, notification_type) 聚合
        # comment_id 应该为 None（当前只支持文章点赞）
        if post_id:
            existing_notification = base_query.filter(
                Notification.post_id == post_id,
                Notification.comment_id.is_(None),
            ).first()

    elif notification_type == NotificationType.COMMENT:
        # 评论通知：需要区分文章评论和评论回复
        if comment_id and post_id:
            # 判断：是评论回复（COMMENT_REPLIED）还是文章评论（POST_COMMENTED）
            # 通过检查 comment_id 的父评论来判断：
            # - 如果 parent_id 存在 → 是评论回复，基于 comment_id 聚合
            # - 如果 parent_id 为 None → 是文章评论，基于 post_id 聚合

            # 简化方案：先尝试基于 comment_id（评论回复）
            existing_notification = base_query.filter(
                Notification.comment_id == comment_id,
            ).first()

            # 如果没有找到，尝试基于 post_id（文章评论）
            # 注意：这需要确保调用时对于 POST_COMMENTED，comment_id 应传 None
            if not existing_notification and post_id:
                existing_notification = base_query.filter(
                    Notification.post_id == post_id,
                    Notification.comment_id.is_(None),
                ).first()
        elif post_id:
            # 只有 post_id，没有 comment_id → 文章评论
            existing_notification = base_query.filter(
                Notification.post_id == post_id,
                Notification.comment_id.is_(None),
            ).first()

    elif notification_type == NotificationType.FOLLOW:
        # 关注通知：基于 (recipient_id, notification_type) 聚合
        # post_id 和 comment_id 都应为 None
        existing_notification = base_query.filter(
            Notification.post_id.is_(None),
            Notification.comment_id.is_(None),
        ).first()

    # Step 3: 如果找到现有通知且在聚合窗口内 → 更新聚合计数
    if existing_notification and _should_aggregate_notification(
        existing_notification, notification_type
    ):
        # 聚合：使用原子操作增加计数，避免并发问题
        db.query(Notification).filter(
            Notification.id == existing_notification.id
        ).update(
            {
                "aggregated_count": Notification.aggregated_count + 1,
                "last_updated_at": datetime.now(UTC),
                "actor_id": actor_id,  # 更新为最新的操作者（用于显示消息）
            }
        )
        db.refresh(existing_notification)

        return existing_notification

    # Step 4: 否则 → 创建新通知
    # 对于文章评论（POST_COMMENTED），comment_id 设为 None 以实现聚合
    # 对于评论回复（COMMENT_REPLIED），保留 comment_id
    new_notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
        # 对于文章评论，comment_id 设为 None 以实现基于文章的聚合
        comment_id=None
        if (
            notification_type == NotificationType.COMMENT and post_id and not comment_id
        )
        else comment_id,
        aggregated_count=1,
    )
    db.add(new_notification)
    db.flush()

    # ⚠️ 这里没有 db.commit()，让调用者来决定何时 commit
    return new_notification


def get_notifications(
    db: Session,
    user_id: UUID,
    pagination_params: PaginationParams,
    *,
    is_read: bool | None = None,
) -> tuple[list[Notification], int]:
    """获取通知列表(分页)

    Args:
        db: 数据库会话
        user_id: 用户ID
        pagination_params: 分页参数，
            默认值为 PaginationParams(page=1, size=20, sort="created_at", order="desc")
        is_read: 是否已读（可选）

    Returns:
        tuple[list[Notification], int]: 通知列表和总记录数
    """
    # 1. 构建基础查询
    query = (
        select(Notification)
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.post).selectinload(Post.author),
        )
        .where(Notification.recipient_id == user_id)
    )

    # 2. 应用过滤条件
    if is_read is not None:
        query = query.where(Notification.is_read.is_(is_read))

    # 3. 执行分页
    items, total = paginate_query(db, query, pagination_params, model=Notification)

    # 4. 在Notification中挂载 message 临时字段，方便构建 NotificationResponse 列表
    for notification in items:
        notification.message = _build_notification_message(notification)

    return items, total


def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification:
    """单条通知设为已读，更新 is_read 与 read_at

    Args:
        db: 数据库会话
        notification_id: 通知ID
        user_id: 用户ID

    Returns:
        Notification: 通知对象（带临时字段 message）
    """
    # 1. 查询通知
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
        )
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.post).selectinload(Post.author),
        )
        .first()
    )
    if not notification:
        raise ResourceNotFoundError("通知")

    # 2. 如果通知未读，则设为已读
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(notification)

    # 3. 添加 message 临时字段，方便构建 NotificationResponse 列表
    notification.message = _build_notification_message(notification)

    return notification


def mark_all_as_read(db: Session, user_id: UUID) -> int:
    """批量把当前用户的所有未读通知设为已读

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        int: 返回受影响的行数（便于提示“本次标记了多少条”）
    """
    updated_rows = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == user_id,
            Notification.is_read.is_(False),
        )
        .update(
            {
                "is_read": True,
                "read_at": datetime.now(UTC),
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return updated_rows


def get_unread_count(db: Session, user_id: UUID) -> int:
    """获取当前用户的未读通知数量（用于角标显示）

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        int: 未读通知数量
    """
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_id == user_id,
            Notification.is_read.is_(False),
        )
        .count()
    )


def delete_notification(
    db: Session, notification_id: UUID, user_id: UUID | None = None
) -> None:
    """删除单条通知（通常用于“清理通知”场景）。

    Args:
        db: 数据库会话
        notification_id: 通知ID
        user_id: 用户ID（可选，用于权限校验）

    Returns:
        None: 无返回值
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
        )
        .first()
    )
    if not notification:
        raise ResourceNotFoundError("通知")

    db.delete(notification)
    db.commit()

    return None


def cleanup_old_notifications(db: Session, days: int = 30) -> int:
    """清理 N 天前的已读通知

    触发清理时机：系统自动触发，可以设置为每天凌晨自动清理

    Args:
        db: 数据库会话
        days: 清理天数（默认30天）

    Returns:
        int: 删除的通知数量
    """
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    # 只删除已读且创建时间超过N天的通知
    query = db.query(Notification).filter(
        Notification.is_read, Notification.created_at < cutoff_date
    )

    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return deleted_count


def _build_notification_message(notification: Notification) -> str:
    """构建通知消息，支持聚合显示

    Args:
        notification: 通知对象

    Returns:
        str: 通知消息，支持聚合显示
    """

    actor_name = notification.actor.nickname or notification.actor.username
    # 点赞通知
    if notification.notification_type == NotificationType.LIKE:
        post_title = notification.post.title if notification.post else "你的文章"
        base = f"{actor_name} 赞了你的文章《{post_title}》"
    # 评论通知
    elif notification.notification_type == NotificationType.COMMENT:
        post_title = notification.post.title if notification.post else "你的文章"
        base = f"{actor_name} 评论了你的文章《{post_title}》"
    # 关注通知
    elif notification.notification_type == NotificationType.FOLLOW:
        base = f"{actor_name} 关注了你"
    # 其他通知
    else:
        base = actor_name

    if notification.aggregated_count > 1:
        base = base.replace(
            actor_name, f"{actor_name} 等 {notification.aggregated_count} 人"
        )

    return base
