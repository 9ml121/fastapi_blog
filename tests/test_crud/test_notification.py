from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.crud import notification as notification_crud
from app.models.comment import Comment
from app.models.notification import Notification, NotificationType
from app.models.post import Post
from app.models.user import User


def test_cleanup_old_notifications(session: Session, sample_user, sample_admin) -> None:
    now = datetime.now(UTC)

    old_notification = Notification(
        recipient_id=sample_user.id,
        actor_id=sample_admin.id,
        notification_type=NotificationType.LIKE,
        aggregated_count=1,
        is_read=True,
        created_at=now - timedelta(days=45),
        last_updated_at=now - timedelta(days=45),
        read_at=now - timedelta(days=44),
    )
    fresh_notification = Notification(
        recipient_id=sample_user.id,
        actor_id=sample_admin.id,
        notification_type=NotificationType.LIKE,
        aggregated_count=1,
        is_read=True,
        created_at=now - timedelta(days=10),
        last_updated_at=now - timedelta(days=10),
        read_at=now - timedelta(days=9),
    )

    session.add_all([old_notification, fresh_notification])
    session.commit()

    old_notification_id = old_notification.id
    fresh_notification_id = fresh_notification.id

    deleted_count = notification_crud.cleanup_old_notifications(session, days=30)

    assert deleted_count == 1
    assert session.get(Notification, old_notification_id) is None
    assert session.get(Notification, fresh_notification_id) is not None


def test_follow_notifications_aggregate(
    session: Session, sample_user: User, sample_user_data: Callable[[], dict[str, str]]
) -> None:
    follower_one = User(**sample_user_data())
    follower_two = User(**sample_user_data())
    session.add_all([follower_one, follower_two])
    session.commit()

    notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=follower_one.id,
        notification_type=NotificationType.FOLLOW,
    )
    session.commit()
    session.refresh(notification)
    first_updated_at = notification.last_updated_at

    aggregated_notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=follower_two.id,
        notification_type=NotificationType.FOLLOW,
    )
    session.commit()
    session.refresh(notification)

    assert aggregated_notification.id == notification.id
    assert notification.aggregated_count == 2
    assert notification.last_updated_at >= first_updated_at


def test_follow_notifications_outside_window_creates_new_record(
    session: Session, sample_user: User, sample_user_data: Callable[[], dict[str, str]]
) -> None:
    follower_one = User(**sample_user_data())
    follower_two = User(**sample_user_data())
    follower_three = User(**sample_user_data())
    session.add_all([follower_one, follower_two, follower_three])
    session.commit()

    notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=follower_one.id,
        notification_type=NotificationType.FOLLOW,
    )
    session.commit()
    session.refresh(notification)

    notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=follower_two.id,
        notification_type=NotificationType.FOLLOW,
    )
    session.commit()
    session.refresh(notification)

    notification.last_updated_at = datetime.now(UTC) - timedelta(days=2)
    session.add(notification)
    session.commit()

    new_notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=follower_three.id,
        notification_type=NotificationType.FOLLOW,
    )
    session.commit()
    session.refresh(new_notification)

    assert new_notification.id != notification.id
    assert new_notification.aggregated_count == 1
    assert session.get(Notification, notification.id) is not None


def test_like_notifications_outside_window_creates_new_record(
    session: Session,
    sample_user: User,
    sample_user_data: Callable[[], dict[str, str]],
    sample_post: Post,
) -> None:
    liker_one = User(**sample_user_data())
    liker_two = User(**sample_user_data())
    liker_three = User(**sample_user_data())
    session.add_all([liker_one, liker_two, liker_three])
    session.commit()

    notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=liker_one.id,
        notification_type=NotificationType.LIKE,
        post_id=sample_post.id,
    )
    session.commit()
    session.refresh(notification)

    notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=liker_two.id,
        notification_type=NotificationType.LIKE,
        post_id=sample_post.id,
    )
    session.commit()
    session.refresh(notification)

    notification.last_updated_at = datetime.now(UTC) - timedelta(hours=3)
    session.add(notification)
    session.commit()

    new_notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=liker_three.id,
        notification_type=NotificationType.LIKE,
        post_id=sample_post.id,
    )
    session.commit()
    session.refresh(new_notification)

    assert new_notification.id != notification.id
    assert new_notification.aggregated_count == 1
    assert session.get(Notification, notification.id) is not None


def test_like_notifications_aggregate(
    session: Session,
    sample_user: User,
    sample_user_data: Callable[[], dict[str, str]],
    sample_post: Post,
) -> None:
    liker_one = User(**sample_user_data())
    liker_two = User(**sample_user_data())
    session.add_all([liker_one, liker_two])
    session.commit()

    notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=liker_one.id,
        notification_type=NotificationType.LIKE,
        post_id=sample_post.id,
    )
    session.commit()
    session.refresh(notification)
    first_updated_at = notification.last_updated_at

    aggregated_notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=liker_two.id,
        notification_type=NotificationType.LIKE,
        post_id=sample_post.id,
    )
    session.commit()
    session.refresh(notification)

    refreshed_notification = session.get(Notification, notification.id)
    assert refreshed_notification is not None
    assert aggregated_notification.id == notification.id
    assert refreshed_notification.aggregated_count == 2
    assert refreshed_notification.last_updated_at >= first_updated_at


def test_comment_notifications_aggregate(
    session: Session,
    sample_user: User,
    sample_user_data: Callable[[], dict[str, str]],
    sample_post: Post,
) -> None:
    parent_comment = Comment(
        content="原始评论",
        user_id=sample_user.id,
        post_id=sample_post.id,
        parent_id=None,
        is_approved=True,
    )
    session.add(parent_comment)

    replier_one = User(**sample_user_data())
    replier_two = User(**sample_user_data())
    session.add_all([replier_one, replier_two])
    session.commit()
    session.refresh(parent_comment)

    notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=replier_one.id,
        notification_type=NotificationType.COMMENT,
        post_id=sample_post.id,
        comment_id=parent_comment.id,
    )
    session.commit()
    session.refresh(notification)
    first_updated_at = notification.last_updated_at

    aggregated_notification = notification_crud.create_or_update_notification(
        db=session,
        recipient_id=sample_user.id,
        actor_id=replier_two.id,
        notification_type=NotificationType.COMMENT,
        post_id=sample_post.id,
        comment_id=parent_comment.id,
    )
    session.commit()
    session.refresh(notification)

    assert aggregated_notification.id == notification.id
    assert notification.comment_id == parent_comment.id
    assert notification.aggregated_count == 2
    assert notification.last_updated_at >= first_updated_at
