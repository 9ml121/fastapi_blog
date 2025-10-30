# Phase 6.4 通知系统 - 概要设计

> **设计目标**：实现通知系统和关注功能，让用户及时了解社交活动，支持用户关注自己感兴趣的创作者
> **预估工作量**：3-4 天（包含 Follow 功能）
> **技术重点**：事件触发机制、通知聚合设计、去重策略、自动清理机制

---

## 1. 业务逻辑与用户故事

### 1.1 核心场景

**用户视角（通知）**：

-   有人点赞我的文章 → 收到通知"用户 A 赞了你的文章《xxx》"
-   有人评论我的文章 → 收到通知"用户 B 评论了你的文章《xxx》"
-   有人关注我 → 收到通知"用户 C 开始关注你"
-   进入通知中心，查看所有未读通知
-   点击通知，快速跳转到相关内容
-   标记通知已读，清理过期通知

**用户视角（关注）**：

-   浏览优质创作者，点击"关注"按钮关注他们
-   在个人资料页查看我的粉丝和关注列表
-   取消关注某个不感兴趣的用户
-   查看关注用户的最新文章

**作者视角**：

-   在仪表板查看交互统计（今日新增点赞数、评论数、粉丝数等）
-   了解哪些内容更能吸引粉丝关注

### 1.2 业务规则

**通知创建规则**：

-   ✅ 点赞文章时 → 创建"点赞"通知给文章作者
-   ✅ 评论文章时 → 创建"评论"通知给文章作者
-   ✅ 关注用户时 → 创建"关注"通知给被关注用户
-   ❌ 用户对自己的行为不产生通知（自己点赞自己的文章无通知）

**通知去重与聚合规则（更新）**：

-   同一文章的多次点赞（1 小时内）→ 聚合为 1 条通知，显示"X 人赞了你的文章"
-   同一文章的多条评论（1 小时内）→ 聚合为 1 条通知，显示"X 人评论了你的文章"
-   关注通知（24 小时内）→ 聚合显示，显示"X 人开始关注你"
-   超过聚合窗口的操作 → 创建新通知
-   **关键改进**：不再限制发起人必须相同，减少通知噪音

**关注规则**：

-   ✅ 用户可以关注其他用户（除自己外）
-   ✅ 同一用户只能关注另一用户一次（唯一约束）
-   ✅ 可以取消关注
-   ✅ 支持查看粉丝列表和关注列表

**通知生命周期**：

-   ✅ 创建：自动创建
-   ✅ 已读状态：支持标记已读/未读
-   ✅ 保留时间：30 天后自动清理已读通知
-   ✅ 删除：用户可手动删除单条或全部通知

---

## 2. 技术选型与架构设计

### 2.1 数据模型设计

#### 关注模型（Follow）

```python
class Follow(Base):
    """用户关注关系模型"""
    __tablename__ = "follows"

    # 主键
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # 关键字段
    follower_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="关注者ID"
    )
    followed_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="被关注者ID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="关注时间"
    )

    # 索引优化
    __table_args__ = (
        # 唯一约束：防止重复关注
        UniqueConstraint("follower_id", "followed_id", name="uq_follow_unique"),
        # 索引：查询某用户的粉丝列表
        Index("idx_followed_created", "followed_id", "created_at"),
        # 索引：查询某用户的关注列表
        Index("idx_follower_created", "follower_id", "created_at"),
    )

    # 关系映射
    follower: Mapped["User"] = relationship(
        foreign_keys=[follower_id],
        back_populates="following",
        lazy="joined",
    )
    followed: Mapped["User"] = relationship(
        foreign_keys=[followed_id],
        back_populates="followers",
        lazy="joined",
    )
```

**设计要点**：

-   ⭐ **唯一约束防重**：同一关注关系只能存在一次
-   📊 **双向索引**：加速粉丝列表和关注列表查询
-   🎯 **自向引用**：用户关注用户，需要两个外键到同一表

#### 通知类型（NotificationType 枚举）

```python
class NotificationType(str, Enum):
    """通知类型枚举"""
    LIKE = "like"           # 点赞
    COMMENT = "comment"     # 评论
    FOLLOW = "follow"       # 关注
    # 后续可扩展：REPLY = "reply", MENTION = "mention" 等
```

#### Notification 模型（含聚合设计）

```python
class Notification(Base):
    """通知记录模型"""
    __tablename__ = "notifications"

    # 主键
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # 关键字段
    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="通知接收人ID"
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="操作发起人ID"
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        comment="通知类型：like, comment, follow"
    )

    # 关联资源（可选，根据通知类型）
    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联的文章ID（点赞、评论类通知）"
    )
    comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联的评论ID（仅评论通知）"
    )

    # 聚合字段（核心设计）
    aggregated_count: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="聚合操作数（同一资源1小时内的多个操作合并为1条）"
    )

    # 状态字段
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True,
        comment="是否已读"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        index=True, comment="通知创建时间"
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="通知最后更新时间（用于聚合判断，1小时内视为同一批操作）"
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="标记已读的时间"
    )

    # 索引优化查询性能
    __table_args__ = (
        # 查询用户的所有通知（按创建时间倒序）
        Index("idx_recipient_created", "recipient_id", "created_at"),
        # 查询用户的未读通知（加速频繁的未读查询）
        Index("idx_recipient_unread", "recipient_id", "is_read", "created_at"),
        # 去重检查：同一资源的通知（用于聚合判断）
        # 注意：移除了 actor_id 限制，支持多用户操作的聚合
        UniqueConstraint(
            "recipient_id", "post_id", "comment_id", "notification_type",
            name="uq_notification_unique"
        ),
    )

    # 关系映射
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id],
        back_populates="received_notifications",
    )
    actor: Mapped["User"] = relationship(
        foreign_keys=[actor_id],
        back_populates="sent_notifications",
    )
    post: Mapped["Post | None"] = relationship(back_populates="notifications")
    comment: Mapped["Comment | None"] = relationship(back_populates="notifications")
```

**聚合设计核心**：

-   ⭐ **aggregated_count 字段**：记录合并的操作数
-   ⭐ **last_updated_at 字段**：`onupdate=func.now()` 自动维护最近聚合时间
-   📊 **复合唯一约束**：`(recipient_id, post_id, comment_id, notification_type)` 确保资源维度唯一，可兼容纯文章聚合（`comment_id=None`）与具体评论通知

#### User 模型扩展

```python
class User(Base):
    # ... existing fields ...

    # 关注关系
    followers: Mapped[list["Follow"]] = relationship(
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
        order_by="desc(Follow.created_at)",
    )
    following: Mapped[list["Follow"]] = relationship(
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
        order_by="desc(Follow.created_at)",
    )

    # 通知关系
    received_notifications: Mapped[list["Notification"]] = relationship(
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        cascade="all",
        order_by="desc(Notification.created_at)",
    )
    sent_notifications: Mapped[list["Notification"]] = relationship(
        foreign_keys="Notification.actor_id",
        back_populates="actor",
        cascade="all",
    )
```

#### Post 模型扩展

````python
class Post(Base):
    # ... existing fields ...

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )

#### Comment 模型扩展

```python
class Comment(Base):
    # ... existing fields ...

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="comment",
        cascade="all, delete-orphan",
        order_by="desc(Notification.created_at)",
    )
````

**设计要点补充**：

-   评论删除时级联清理相关通知，避免悬空引用
-   与 `Notification.comment` 的 `back_populates` 一致，保持 ORM 映射稳定

#### PostView 模型回顾（支撑通知）

```python
class PostView(Base):
    # ... existing fields ...

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        comment="浏览用户ID（NULL 表示匿名用户）",
    )
```

**设计要点补充**：

-   `ondelete="SET NULL"`：删除用户后保留浏览轨迹，方便通知与推荐做行为分析
-   保持匿名浏览的兼容性，避免历史 `PostView` 记录丢失

---

## 3. CRUD 操作设计

### 3.1 关注功能 CRUD

| 操作             | 函数签名                                      | 说明                       |
| ---------------- | --------------------------------------------- | -------------------------- |
| **关注用户**     | `follow_user(db, follower_id, followed_id)`   | 建立关注关系，自动创建通知 |
| **取消关注**     | `unfollow_user(db, follower_id, followed_id)` | 删除关注关系               |
| **检查是否关注** | `is_following(db, follower_id, followed_id)`  | 查询关注状态               |
| **获取粉丝列表** | `get_followers(db, user_id, limit, offset)`   | 分页查询粉丝               |
| **获取关注列表** | `get_following(db, user_id, limit, offset)`   | 分页查询关注用户           |
| **获取粉丝数**   | `get_follower_count(db, user_id)`             | 快速查询粉丝数             |

### 3.2 通知功能 CRUD（含聚合）

| 操作             | 函数签名                                                                               | 说明                        |
| ---------------- | -------------------------------------------------------------------------------------- | --------------------------- |
| **创建通知**     | `create_or_update_notification(db, recipient_id, actor_id, type, post_id, comment_id)` | 自动聚合（1 小时内合并）    |
| **获取通知列表** | `get_notifications(db, user_id, is_read=None, limit, offset)`                          | 分页查询，支持已读/未读过滤 |
| **标记已读**     | `mark_as_read(db, notification_id)`                                                    | 单条标记已读                |
| **批量标记已读** | `mark_all_as_read(db, user_id)`                                                        | 批量标记全部已读            |
| **获取未读数**   | `get_unread_count(db, user_id)`                                                        | 快速查询未读通知数          |
| **删除通知**     | `delete_notification(db, notification_id)`                                             | 删除单条通知                |
| **清理过期通知** | `cleanup_old_notifications(db, days=30)`                                               | 删除 30 天前的已读通知      |

### 3.3 事件驱动模式设计

**核心概念**：采用事件驱动架构，在关键业务操作（点赞、评论、关注）后自动触发通知创建，实现解耦和可扩展性。

#### 事件类型定义

```python
from enum import Enum

class NotificationEvent(str, Enum):
    """业务事件类型"""
    POST_LIKED = "post_liked"           # 文章被点赞
    POST_COMMENTED = "post_commented"   # 文章被评论
    USER_FOLLOWED = "user_followed"     # 用户被关注
    # 后续可扩展：COMMENT_REPLIED, POST_MENTIONED 等
````

#### 事件发射模式

```python
# 在 CRUD 层操作后自动发射事件
def toggle_like(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """点赞/取消点赞（含事件触发）"""
    # ... 原有点赞逻辑 ...
    like = PostLike(user_id=user_id, post_id=post_id)
    db.add(like)
    db.commit()

    # 🎯 事件驱动：点赞成功后自动触发通知事件
    post = get_post_by_id(db, post_id)
    if post.author_id != user_id:  # 不给自己发通知
        _emit_notification_event(
            event_type=NotificationEvent.POST_LIKED,
            recipient_id=post.author_id,
            actor_id=user_id,
            post_id=post_id,
            db=db
        )

    return True
```

#### 事件处理器（Event Handler）

```python
def _emit_notification_event(
    event_type: NotificationEvent,
    recipient_id: UUID,
    actor_id: UUID,
    post_id: UUID | None = None,
    comment_id: UUID | None = None,
    db: Session = None,
) -> Notification:
    """统一的事件处理器，处理通知创建和聚合"""

    # 映射事件类型到通知类型
    event_to_notification_type = {
        NotificationEvent.POST_LIKED: NotificationType.LIKE,
        NotificationEvent.POST_COMMENTED: NotificationType.COMMENT,
        NotificationEvent.USER_FOLLOWED: NotificationType.FOLLOW,
    }

    notification_type = event_to_notification_type[event_type]

    # 调用聚合创建函数
    return create_or_update_notification(
        db=db,
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
        comment_id=comment_id,
    )
```

### 3.4 通知粒度设计与去重策略

**问题**：如何平衡用户体验和通知刷屏？

**解决方案**：通过聚合和去重策略实现精准通知。

#### 通知粒度矩阵（更新）

| 事件类型 | 粒度     | 去重策略                  | 聚合策略                   | 示例                 |
| -------- | -------- | ------------------------- | -------------------------- | -------------------- |
| **点赞** | 文章维度 | 同一文章只有 1 条通知     | 1 小时内所有用户的点赞合并 | "3 人赞了你的文章"   |
| **评论** | 文章维度 | 同一文章只有 1 条通知     | 1 小时内所有用户的评论合并 | "2 人评论了你的文章" |
| **关注** | 用户维度 | 同一被关注者只有 1 条通知 | 24 小时内所有关注合并      | "5 人开始关注你"     |

**关键改进**：

-   移除了对发起人的限制，支持多用户操作的聚合
-   关注通知使用更长的聚合窗口（24 小时）
-   减少通知数量，提升用户体验

#### 具体去重规则

```python
# 规则 1：点赞通知去重 - 同一用户对同一文章
# UniqueConstraint: (recipient_id, actor_id, post_id, notification_type='LIKE')
# 若重复点赞，直接忽略（业务层已处理 PostLike 的唯一约束）

# 规则 2：评论通知不去重 - 每条评论独立通知
# 同一用户的多条评论 → 多条独立通知

# 规则 3：关注通知去重 - 同一用户对同一被关注者
# UniqueConstraint: (recipient_id, actor_id, notification_type='FOLLOW', post_id=NULL)
# 若重复关注，触发 onconflict 更新聚合计数
```

#### 聚合触发条件

```python
def should_aggregate_notification(
    existing_notification: Notification,
    current_time: datetime,
    notification_type: NotificationType,
) -> int:
    """判断是否应该聚合到现有通知

    触发聚合的条件（更新）：
    1. 通知类型相同（LIKE, COMMENT, FOLLOW）
    2. 资源相同（post_id 或 recipient_id for FOLLOW）
    3. 时间在聚合窗口内：
       - 点赞/评论：1 小时
       - 关注：24 小时

    Args:
        existing_notification: 现有通知
        current_time: 当前时间
        notification_type: 通知类型

    Returns:
        int: 聚合窗口时间（秒）
    """
    # 不同类型使用不同的聚合窗口
    aggregation_windows = {
        NotificationType.LIKE: 3600,      # 1小时
        NotificationType.COMMENT: 3600,   # 1小时
        NotificationType.FOLLOW: 86400,   # 24小时
    }

    aggregation_window = aggregation_windows.get(notification_type, 3600)
    time_diff = (current_time - existing_notification.last_updated_at).total_seconds()

    return time_diff < aggregation_window
```

#### 聚合计数更新流程

```python
def create_or_update_notification(
    db: Session,
    recipient_id: UUID,
    actor_id: UUID,
    notification_type: NotificationType,
    post_id: UUID | None = None,
    comment_id: UUID | None = None,
) -> Notification:
    """创建或更新通知，支持聚合

    流程：
    1. 查询是否存在相同的通知（recipient  + type + post）
    2. 如果存在 + 在聚合窗口内 → 更新聚合计数
    3. 否则 → 创建新通知
    """

    # Step 1: 构建查询条件（更新：移除actor_id限制）
    query = db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.notification_type == notification_type,
        Notification.post_id == post_id,
    )

    existing_notification = query.first()

    # Step 2: 判断是否聚合
    if existing_notification:
        if should_aggregate_notification(existing_notification, datetime.now(UTC), notification_type):
            # 聚合：使用原子操作增加计数，避免并发问题
            db.query(Notification).filter(
                Notification.id == existing_notification.id
            ).update({
                "aggregated_count": Notification.aggregated_count + 1,
                "last_updated_at": datetime.now(UTC)
            })
            db.commit()
            db.refresh(existing_notification)
            return existing_notification
        # 否则创建新通知（超过聚合窗口）

    # Step 3: 创建新通知
    new_notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
        comment_id=comment_id,
        aggregated_count=1,
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification
```

### 3.5 触发机制集成

**在相关 CRUD 操作中嵌入事件驱动**：

```python
# 在 app/crud/post_like.py 中
from app.crud.notification import _emit_notification_event

def toggle_like(db: Session, user_id: UUID, post_id: UUID) -> bool:
    """点赞/取消点赞，含事件驱动"""

    # 1. 查询现有点赞
    existing_like = db.query(PostLike).filter(
        PostLike.user_id == user_id,
        PostLike.post_id == post_id,
    ).first()

    post = get_post_by_id(db, post_id)

    if existing_like:
        # 取消点赞
        db.delete(existing_like)
        post.decrement_like_count()
        db.commit()
        return False  # 已取消
    else:
        # 新增点赞
        like = PostLike(user_id=user_id, post_id=post_id)
        db.add(like)
        post.increment_like_count()
        db.commit()

        # 🎯 事件驱动：发射通知事件
        if post.author_id != user_id:  # 不给自己发通知
            _emit_notification_event(
                event_type=NotificationEvent.POST_LIKED,
                recipient_id=post.author_id,
                actor_id=user_id,
                post_id=post_id,
                db=db,
            )

        return True  # 已添加


# 在 app/crud/comment.py 中
def create_comment(db: Session, comment_in: CommentCreate, author_id: UUID, post_id: UUID) -> Comment:
    """创建评论，含事件驱动"""

    post = get_post_by_id(db, post_id)

    # 1. 创建评论
    comment = Comment(
        content=comment_in.content,
        author_id=author_id,
        post_id=post_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # 🎯 事件驱动：发射通知事件
    if post.author_id != author_id:  # 评论人不是作者
        _emit_notification_event(
            event_type=NotificationEvent.POST_COMMENTED,
            recipient_id=post.author_id,
            actor_id=author_id,
            post_id=post_id,
            comment_id=comment.id,
            db=db,
        )

    return comment


# 在 app/crud/follow.py 中
def follow_user(db: Session, follower_id: UUID, followed_id: UUID) -> bool:
    """关注用户，含事件驱动"""

    # 1. 检查自我关注
    if follower_id == followed_id:
        raise InvalidParametersError(message="不能关注自己")

    # 2. 检查是否已关注
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.followed_id == followed_id,
    ).first()

    if existing_follow:
        raise ResourceConflictError(resource="关注关系")

    # 3. 创建关注
    follow = Follow(follower_id=follower_id, followed_id=followed_id)
    db.add(follow)
    db.commit()

    # 🎯 事件驱动：发射通知事件
    _emit_notification_event(
        event_type=NotificationEvent.USER_FOLLOWED,
        recipient_id=followed_id,
        actor_id=follower_id,
        db=db,
    )

    return True
```

### 3.6 清理机制

**自动清理过期通知**：

```python
def cleanup_old_notifications(db: Session, days: int = 30) -> int:
    """清理 N 天前的已读通知

    Args:
        db: 数据库会话
        days: 清理天数（默认30天）

    Returns:
        int: 删除的通知数量
    """
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    # 只删除已读且创建时间超过N天的通知
    query = db.query(Notification).filter(
        Notification.is_read == True,
        Notification.created_at < cutoff_date
    )

    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return deleted_count
```

**触发清理的时机**（选择一种）：

-   方案 A（推荐）：应用启动时检查一次
-   方案 B：每天午夜定时任务
-   方案 C：用户每次登录时检查

### 3.7 消息模板系统（新增）

**模板设计原则**：

-   支持动态参数替换
-   支持单数/复数形式
-   易于国际化扩展

```python
# 通知消息模板系统
NOTIFICATION_TEMPLATES = {
    # 点赞通知
    "like_single": "{actor} 赞了你的文章《{post_title}》",
    "like_multiple": "{count} 人赞了你的文章《{post_title}》",

    # 评论通知
    "comment_single": "{actor} 评论了你的文章《{post_title}》",
    "comment_multiple": "{count} 人评论了你的文章《{post_title}》",

    # 关注通知
    "follow_single": "{actor} 开始关注你",
    "follow_multiple": "{count} 人开始关注你",
}

def format_notification_message(
    notification_type: str,
    count: int,
    actor_name: str | None = None,
    post_title: str | None = None,
) -> str:
    """格式化通知消息

    Args:
        notification_type: 通知类型
        count: 聚合数量
        actor_name: 主要发起人名称（可选）
        post_title: 文章标题（可选）

    Returns:
        str: 格式化后的通知消息
    """
    template_key = f"{notification_type}_{'multiple' if count > 1 else 'single'}"
    template = NOTIFICATION_TEMPLATES.get(template_key, "")

    return template.format(
        actor=actor_name or "多人",
        count=count,
        post_title=post_title or "某篇文章"
    )
```

**使用示例**：

```python
# 生成通知消息
message = format_notification_message(
    notification_type="like",
    count=3,
    actor_name="张三",
    post_title="FastAPI开发指南"
)
# 结果: "3 人赞了你的文章《FastAPI开发指南》"
```

---

## 4. API 设计

### 4.1 关注 API 端点

| 方法       | 端点                                      | 说明           |
| ---------- | ----------------------------------------- | -------------- |
| **POST**   | `/api/v1/users/{user_id}/follow`          | 关注用户       |
| **DELETE** | `/api/v1/users/{user_id}/follow`          | 取消关注       |
| **GET**    | `/api/v1/users/{user_id}/followers`       | 获取粉丝列表   |
| **GET**    | `/api/v1/users/{user_id}/following`       | 获取关注列表   |
| **GET**    | `/api/v1/users/{user_id}/follower-count`  | 获取粉丝数     |
| **GET**    | `/api/v1/users/me/is-following/{user_id}` | 检查是否已关注 |

### 4.2 通知 API 端点

| 方法         | 端点                                             | 说明                   |
| ---------- | ---------------------------------------------- | -------------------- |
| **GET**    | `/api/v1/users/me/notifications`               | 获取我的通知列表（分页、过滤已读/未读） |
| **GET**    | `/api/v1/users/me/notifications/unread-count`  | 获取未读通知数              |
| **PATCH**  | `/api/v1/users/me/notifications/{id}`          | 标记单条通知已读             |
| **PATCH**  | `/api/v1/users/me/notifications/mark-all-read` | 批量标记全部已读             |
| **DELETE** | `/api/v1/users/me/notifications/{id}`          | 删除通知                 |

### 4.3 响应数据结构

```python
# 关注状态响应
class FollowStatusResponse(BaseModel):
    user_id: UUID = Field(description="用户ID")
    is_following: bool = Field(description="是否已关注")
    follower_count: int = Field(description="粉丝数")
    following_count: int = Field(description="关注数")

# 用户简化响应（用于关注/粉丝列表）
class UserSimpleResponse(BaseModel):
    id: UUID = Field(description="用户ID")
    username: str = Field(description="用户名")
    avatar_url: str | None = Field(description="头像URL")
    bio: str | None = Field(description="个人签名")
    is_following: bool = Field(description="当前用户是否已关注此用户")

# 通知响应模型（含聚合）
class NotificationResponse(BaseModel):
    id: UUID = Field(description="通知ID")
    actor: UserSimpleResponse = Field(description="操作发起人")
    notification_type: NotificationType = Field(description="通知类型")
    message: str = Field(description="通知文案，支持聚合显示")
    aggregated_count: int = Field(description="聚合操作数")
    # 示例：
    # - 单个："用户 A 赞了你的文章《标题》"
    # - 聚合："用户 A 等 3 人赞了你的文章《标题》"
    post: PostResponse | None = Field(description="关联的文章（如有）")
    is_read: bool = Field(description="是否已读")
    created_at: datetime = Field(description="创建时间")
    read_at: datetime | None = Field(description="标记已读的时间")

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("message")
    def serialize_message(self, message: str) -> str:
        """动态生成聚合文案"""
        if self.aggregated_count > 1:
            return message.replace("赞了", f"等 {self.aggregated_count} 人赞了")
        return message
```

---

## 5. 性能与并发考虑

### 5.1 查询优化

-   ✅ **复合索引**：`(recipient_id, is_read, created_at)` 加速未读通知查询
-   ✅ **分页查询**：默认 20 条/页，支持游标分页
-   ✅ **唯一约束防重**：通过数据库约束避免重复通知和关注
-   ✅ **双向索引**：粉丝列表和关注列表查询优化

### 5.2 聚合与去重

**点赞/关注的去重**：

-   使用 `UniqueConstraint` 确保同一用户对同一资源只有一条通知
-   若重复操作 > 1 小时，会创建新通知

**聚合判断**：

```sql
-- 查询是否存在1小时内的同组合通知
SELECT * FROM notifications
WHERE recipient_id = ?
  AND actor_id = ?
  AND notification_type = ?
  AND post_id = ?
  AND last_updated_at > NOW() - INTERVAL 1 hour
LIMIT 1
```

### 5.3 清理策略

-   ⏰ **触发时机**：应用启动时执行一次（或每天午夜）
-   📊 **批量删除**：单次删除 1000+ 条记录，避免长事务
-   💾 **保留已读通知**：只删除已读通知，未读通知永久保留

---

## 6. 实现优先级（更新）

### Phase 6.4.1 - 关注 + 通知基础（第一周，推荐分 2 天）

**第 1 天：模型 + CRUD**

-   ✅ Follow 模型定义 + 迁移
-   ✅ Notification 模型定义（含聚合字段）+ 迁移
-   ✅ Follow CRUD 实现（follow, unfollow, is_following, get_followers/following）
-   ✅ Notification CRUD 实现（create_or_update, get_notifications, mark_as_read, cleanup）

**第 2 天：API + 集成 + 测试**

-   ✅ Follow API 端点
-   ✅ Notification API 端点
-   ✅ 在 toggle_like, create_comment, follow_user 中集成通知创建
-   ✅ 通知清理机制（应用启动）
-   ✅ 完整测试（单元 + 集成 + E2E）

### Phase 6.4.2 - 前端展示与优化（可选）

-   通知中心 UI
-   WebSocket 实时推送（可选）
-   关注用户的专栏订阅

---

## 7. 关键设计决策说明

| 决策项           | 选择                           | 理由                                  |
| ---------------- | ------------------------------ | ------------------------------------- |
| **聚合时间窗口** | 点赞/评论 1 小时，关注 24 小时 | 根据操作频率设置不同的聚合窗口        |
| **聚合粒度**     | 同一资源（不限发起人）         | 减少通知数量，提升用户体验            |
| **去重方案**     | UniqueConstraint + 原子更新    | 数据库层级确保一致性，避免并发问题    |
| **消息模板**     | 参数化模板系统                 | 支持国际化，易于扩展                  |
| **并发安全**     | 原子操作                       | 避免聚合计数的竞态条件                |
| **清理时机**     | 应用启动                       | 简洁可靠，无需额外依赖                |
| **清理保留期**   | 30 天                          | 平衡用户体验和存储空间                |
| **关注自己**     | 不允许                         | 业务层检查 follower_id != followed_id |

---

## 8. 测试策略

### 单元测试

-   Follow CRUD：创建、查询、删除、防重复
-   Notification 聚合：聚合判断、计数更新
-   过期清理：时间判断、删除统计

### 集成测试

-   用户 A 关注用户 B → B 收到"关注"通知
-   用户 A 点赞文章 → 作者收到"点赞"通知
-   1 小时内重复操作 → 通知聚合，aggregated_count 递增
-   超过 1 小时后操作 → 创建新通知
-   标记已读 → 未读数减少

### 端到端测试

-   完整的关注流程
-   完整的通知查看和标记流程
-   聚合通知的显示正确性

---

## 9. 后续扩展空间

-   💡 **WebSocket 实时推送**：通知创建时立即推送给在线用户
-   💡 **通知订阅配置**：用户可自定义接收哪些类型的通知
-   💡 **邮件通知**：关键通知发送邮件提醒
-   💡 **粉丝等级**：区分僵尸粉、活跃粉、VIP 粉等
-   💡 **推荐关注**：基于兴趣推荐相关创作者
-   💡 **关注动态流**：展示关注用户的最新文章和活动

---

## 附录：核心代码框架预览

### Follow 模型位置

-   文件：`app/models/follow.py`
-   导入：`app/models/__init__.py`

### Notification 模型位置

-   文件：`app/models/notification.py`
-   导入：`app/models/__init__.py`

### CRUD 操作位置

-   文件：`app/crud/follow.py`
-   文件：`app/crud/notification.py`

### API 端点位置

-   文件：`app/api/v1/endpoints/follows.py`
-   文件：`app/api/v1/endpoints/notifications.py`

### 测试位置

-   文件：`tests/test_api/test_follows.py`
-   文件：`tests/test_api/test_notifications.py`
