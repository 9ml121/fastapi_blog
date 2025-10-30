"""
Pytest 配置文件 - 定义共享的 fixture

这个文件中的 fixture 会自动对所有测试文件可用，无需显式 import。
"""

import sqlite3
import uuid
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

import app.crud.post as post_crud
from app.core.security import create_access_token
from app.crud import comment as comment_crud
from app.crud import follow as follow_crud
from app.db.database import Base
from app.models import Comment, Post, PostView, Tag, User  # noqa: F401
from app.models.notification import Notification
from app.models.post import PostStatus
from app.models.user import UserRole
from app.schemas.comment import CommentCreate
from app.schemas.post import PostCreate

# ============================================
# 数据库相关 Fixture
# ============================================


@pytest.fixture(scope="function")
def engine() -> Generator[Engine, None, None]:
    """创建测试数据库引擎（内存 SQLite 数据库）

    配置：
    - 使用内存数据库，速度快，测试隔离
    - StaticPool 确保所有连接使用同一个内存数据库
    - 自动启用 SQLite 外键约束（默认关闭）
    - 每个测试函数独立的数据库实例

    Returns:
        Engine: SQLAlchemy 数据库引擎
    """
    # 创建内存数据库引擎，使用 StaticPool 确保单一连接
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 关键：使用 StaticPool 确保所有会话共享同一个连接
    )

    # 启用 SQLite 外键约束（必须在 create_all() 之前）
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(
        dbapi_conn: sqlite3.Connection, _connection_record: ConnectionPoolEntry
    ) -> None:
        """每次建立连接时自动启用外键约束"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 创建所有表
    Base.metadata.create_all(engine)

    yield engine

    # 清理：删除所有表并释放连接
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """创建测试数据库会话

    配置：
    - 每个测试函数独立的会话
    - 测试结束后自动回滚，保证测试隔离

    Args:
        engine: 数据库引擎 fixture

    Returns:
        Session: SQLAlchemy 数据库会话
    """
    # 将引擎绑定到 sessionmaker
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()

    yield session

    # 清理：回滚未提交的事务并关闭会话
    session.rollback()
    session.close()


# ============================================
# 模型数据 Fixture
# ============================================


@pytest.fixture
def sample_user(session: Session) -> User:
    """创建测试用户

    配置：
    - 使用 UUID 确保用户名和邮箱唯一
    - 已提交到数据库，可以直接使用

    Args:
        session: 数据库会话 fixture

    Returns:
        User: 已保存的用户对象
    """
    user = User(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
        nickname="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)  # 刷新以获取数据库生成的字段
    return user


@pytest.fixture
def sample_user_with_password(session: Session) -> tuple[User, str]:
    """创建带有已知明文密码的测试用户（用于密码修改测试）

    配置：
    - 使用真实的密码哈希（bcrypt）
    - 返回用户对象和明文密码的元组
    - 已提交到数据库

    Args:
        session: 数据库会话 fixture

    Returns:
        tuple[User, str]: (用户对象, 明文密码)

    Example:
        >>> def test_password(sample_user_with_password):
        ...     user, plain_password = sample_user_with_password
        ...     # plain_password 是 "TestPassword123!"
    """
    from app.core.security import hash_password

    plain_password = "TestPassword123!"
    user = User(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(plain_password),  # 使用真实的 bcrypt 哈希
        nickname="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, plain_password


@pytest.fixture
def sample_admin(session: Session, sample_user) -> User:
    """创建测试管理员用户"""
    user = User(
        username="test_admin",
        email="test_admin@example.com",
        password_hash="hashed_password",
        nickname="Test Admin",
        role=UserRole.ADMIN,
    )
    session.add(user)
    session.commit()
    session.refresh(user)  # 刷新以获取数据库生成的字段
    return user


@pytest.fixture
def sample_post(session: Session, sample_user: User) -> Post:
    """创建测试文章,默认是草稿状态

    配置：
    - 自动关联 sample_user 作为作者
    - 使用 UUID 确保 slug 唯一
    - 已提交到数据库

    Args:
        session: 数据库会话 fixture
        sample_user: 用户 fixture

    Returns:
        Post: 已保存的文章对象
    """
    post = Post(
        title="Test Post",
        content="This is a test post content.",
        slug=f"test-post-{uuid.uuid4().hex[:8]}",
        author_id=sample_user.id,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@pytest.fixture
def published_post(session: Session, sample_user: User) -> Post:
    """创建一篇已发布文章"""
    # ✅ 使用 CRUD 层创建，自动处理标签字符串转 Tag 对象
    post = Post(
        title="测试已发布文章",
        content="这是一篇已发布文章",
        slug=f"test-published-post-{uuid.uuid4().hex[:8]}",
        status=PostStatus.PUBLISHED,
        author_id=sample_user.id,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@pytest.fixture
def post_view_records(
    session: Session,
    published_post: Post,
    sample_user: User,
) -> dict[str, PostView]:
    """预置文章浏览记录，覆盖不同时间窗口与身份场景"""

    now = datetime.now(UTC)

    recent_user_view = PostView(
        post_id=published_post.id,
        user_id=sample_user.id,
        session_id="user_session_recent",
        ip_address="10.0.0.1",
        viewed_at=now - timedelta(minutes=10),
    )

    stale_user_view = PostView(
        post_id=published_post.id,
        user_id=sample_user.id,
        session_id="user_session_stale",
        ip_address="10.0.0.2",
        viewed_at=now - timedelta(days=2),
    )

    recent_anonymous_view = PostView(
        post_id=published_post.id,
        session_id="anon_session_recent",
        ip_address="203.0.113.10",
        viewed_at=now - timedelta(minutes=5),
    )

    stale_anonymous_view = PostView(
        post_id=published_post.id,
        session_id="anon_session_stale",
        ip_address="203.0.113.20",
        viewed_at=now - timedelta(days=3),
    )

    session.add_all(
        [recent_user_view, stale_user_view, recent_anonymous_view, stale_anonymous_view]
    )
    session.commit()

    for view in (
        recent_user_view,
        stale_user_view,
        recent_anonymous_view,
        stale_anonymous_view,
    ):
        session.refresh(view)

    return {
        "recent_user": recent_user_view,
        "stale_user": stale_user_view,
        "recent_anonymous": recent_anonymous_view,
        "stale_anonymous": stale_anonymous_view,
    }


@pytest.fixture
def draft_post(session: Session, sample_user: User) -> Post:
    """创建一篇草稿文章"""
    post = Post(
        title="草稿文章",
        content="这是一篇草稿文章",
        slug=f"test-draft-post-{uuid.uuid4().hex[:8]}",
        status=PostStatus.DRAFT,
        author_id=sample_user.id,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


# ============================================
# 用于测试 models 原始数据工厂函数 Fixture
# ============================================


@pytest.fixture
def sample_user_data() -> Callable[[], dict[str, str]]:
    """生成唯一的用户数据字典的工厂函数

    用于需要手动创建用户对象的测试场景。
    每次调用都会生成不同的数据，避免唯一性冲突。

    Returns:
        callable: 工厂函数，每次调用返回新的数据字典

    Example:
        >>> def test_multiple_users(sample_user_data):
        ...     user1 = User(**sample_user_data())  # 第一个用户
        ...     user2 = User(**sample_user_data())  # 第二个用户，不同的 username/email
        ...     user3 = User(**{**sample_user_data(), "nickname": "Custom"})  # 定制字段
    """

    def _factory() -> dict[str, str]:
        """生成一个唯一的用户数据字典"""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "password_hash": "hashed_password_123",
            "nickname": f"Test User {unique_id}",
        }

    return _factory


@pytest.fixture
def sample_post_data(sample_user: User) -> Callable[[], dict[str, str | uuid.UUID]]:
    """生成唯一的文章数据字典的工厂函数

    用于需要手动创建文章对象的测试场景。
    每次调用都会生成不同的 slug，避免唯一性冲突。

    Args:
        sample_user: 用户 fixture，提供 author_id

    Returns:
        callable: 工厂函数，每次调用返回新的数据字典

    Example:
        >>> def test_multiple_posts(sample_post_data):
        ...     post1 = Post(**sample_post_data())  # 第一篇文章
        ...     post2 = Post(**sample_post_data())  # 第二篇文章，不同的 slug
        ...     post3 = Post(**{**sample_post_data(), "title": "Custom"})  # 定制字段
    """

    def _factory() -> dict[str, str | uuid.UUID]:
        """生成一个唯一的文章数据字典"""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "title": f"Test Post {unique_id}",
            "content": f"This is test content {unique_id}.",
            "slug": f"test-post-{unique_id}",
            "author_id": sample_user.id,
        }

    return _factory


# ============================================
# API 测试客户端 Fixture
# ============================================


@pytest.fixture(scope="function")
def client(session) -> Generator[TestClient, None, None]:
    """创建测试客户端，并覆盖 get_db 依赖

    注意：
    - 使用 engine 创建独立的 session factory
    - 每次请求都会创建新的 session
    - engine 已经创建了所有表
    """
    from app.api.deps import get_db
    from app.main import app

    # 覆盖依赖
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as test_client:
        yield test_client

    # 清理覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    """生成认证 headers（直接生成 token，不调用登录接口）"""
    token = create_access_token(data={"sub": str(sample_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(sample_admin: User) -> dict:
    """管理员认证 headers fixture"""
    token = create_access_token(data={"sub": str(sample_admin.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================
# 多个user、post、comment数据 Fixture
# ============================================
@pytest.fixture
def sample_users(session: Session, sample_user: User) -> list[User]:
    """创建多个测试用户，包含 sample_user

    创建 3 个额外的测试用户，用于：
    - 测试用户 API 端点
    - 作为文章和评论的作者
    - 创建sample_follows测试数据
    """
    from app.crud.user import create_user
    from app.schemas.user import UserCreate

    users = [sample_user]
    user_templates = [
        {
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "password": "testpassword123",
        },
        {
            "username": "lisi",
            "email": "lisi@example.com",
            "password": "testpassword123",
        },
        {
            "username": "wangwu",
            "email": "wangwu@example.com",
            "password": "testpassword123",
        },
    ]

    for template in user_templates:
        user_data = UserCreate(**template)
        user = create_user(session, user_in=user_data)
        users.append(user)

    return users


@pytest.fixture
def sample_posts(session: Session, sample_user: User) -> list[Post]:
    """创建多样化的测试文章数据

    - 4个published文章 + 2个draft文章 + 1个archived文章
    - 使用 sample_user 作为作者
    - 不同标签（Python, FastAPI, Web开发, 教程, 实战）
    - 不同发布状态（已发布、草稿、 归档）
    - 不同发布时间（分散在最近30天内）
    - 不同标题内容（便于测试模糊搜索）
    """

    # 定义测试数据模板
    post_templates = [
        # 已发布的文章
        {
            "title": "Python 入门教程",
            "content": "Python 是一门简单易学的编程语言...",
            "summary": "Python 基础语法介绍",
            "tags": ["Python", "教程"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": None,  # 25天前发布
        },
        {
            "title": "FastAPI 快速开发指南",
            "content": "FastAPI 是现代 Python Web 框架...",
            "summary": "FastAPI 核心特性介绍",
            "tags": ["FastAPI", "Web开发"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -20,
        },
        {
            "title": "Web 开发最佳实践",
            "content": "现代 Web 开发需要考虑很多因素...",
            "summary": "Web 开发经验总结",
            "tags": ["Web开发", "实战"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -15,
        },
        {
            "title": "Python 数据分析实战",
            "content": "使用 Python 进行数据分析...",
            "summary": "数据分析项目实战",
            "tags": ["Python", "实战"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -10,
        },
        # 归档文章
        {
            "title": "FastAPI 性能优化技巧",
            "content": "如何优化 FastAPI 应用性能...",
            "summary": "性能优化经验分享",
            "tags": ["FastAPI", "性能"],
            "status": PostStatus.ARCHIVED,
            "published_at_offset": -5,
        },
        # 草稿文章
        {
            "title": "Django vs FastAPI 对比",
            "content": "Django 和 FastAPI 的详细对比...",
            "summary": "框架对比分析",
            "tags": ["Django", "FastAPI"],
            "status": PostStatus.DRAFT,
            "published_at_offset": -1,
        },
        {
            "title": "Python 异步编程详解",
            "content": "深入理解 Python 异步编程...",
            "summary": "异步编程概念解析",
            "tags": ["Python", "异步"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
    ]

    posts = []
    base_time = datetime.now()

    for _, template in enumerate(post_templates):
        # 创建文章
        post_in = PostCreate(
            title=template["title"],
            content=template["content"],
            summary=template["summary"],
            tags=template["tags"],
        )

        post = post_crud.create_post(
            db=session, post_in=post_in, author_id=sample_user.id
        )

        # 手动设置发布状态和发布时间
        post.status = template["status"]
        if template["published_at_offset"] is not None:
            post.published_at = base_time + timedelta(
                days=template["published_at_offset"]
            )

        session.add(post)
        posts.append(post)

    session.commit()
    return posts


@pytest.fixture
def sample_comments(
    session: Session, sample_post: Post, sample_user: User
) -> list[Comment]:
    """创建sample_post多样化评论数据

    结构:
    - 评论1 (顶级)
      - 评论2 (回复评论1)
      - 评论3 (回复评论1)
    - 评论4 (顶级)
    - 评论5 (顶级)
    """
    # 定义5 条 评论数据模板
    comment_templates = [
        {
            "content": "这篇文章写得很好，学到了很多！",
            "parent_id": None,  # 顶级评论
            "time_offset": -6,
        },
        {
            "content": "回复楼上1",
            "parent_id": "dynamic",  # 回复第1条评论,
            "time_offset": -5,
        },
        {
            "content": "回复楼上2",
            "parent_id": "dynamic",  # 回复第 1条评论,
            "time_offset": -4,
        },
        {
            "content": "FastAPI 确实比 Django 更现代",
            "parent_id": None,
            "time_offset": -5,
        },
        {
            "content": "同意，性能也更好",
            "parent_id": None,
            "time_offset": -4,
        },
    ]

    comments = []
    base_time = datetime.now()

    for i, template in enumerate(comment_templates):
        # 处理动态 parent_id 引用
        parent_id = template["parent_id"]
        if parent_id == "dynamic":
            parent_id = comments[0].id if i == 1 or i == 2 else None

        # 创建评论
        comment_in = CommentCreate(
            content=template["content"],
            parent_id=parent_id,
        )

        comment = comment_crud.create_comment(
            db=session,
            obj_in=comment_in,
            author_id=sample_user.id,
            post_id=sample_post.id,
        )

        # 手动设置发布时间
        comment.created_at = base_time + timedelta(days=template["time_offset"])

        session.add(comment)
        comments.append(comment)

    session.commit()
    return comments


# ============================================
# 关注测试数据 Fixture
# ============================================
@pytest.fixture
def sample_follows(session: Session, sample_users: list[User]) -> list[User]:
    """创建sample_users之间的关注关系

    sample_users[0]之外的3 个用户都关注sample_users[0]
    """
    sample_user = sample_users[0]
    for user in sample_users[1:]:
        follow_crud.follow_user(
            db=session,
            follower_id=user.id,
            followed_id=sample_user.id,
        )

    return sample_users


# ============================================
# 通知测试数据 Fixture
# ============================================


@dataclass(slots=True)
class CreatedNotifications:
    """用于封装通知工厂返回结果的数据类"""

    all: list[Notification]
    read: list[Notification]
    unread: list[Notification]

    @property
    def all_count(self) -> int:
        return len(self.all)

    @property
    def unread_count(self) -> int:
        return len(self.unread)

    @property
    def read_count(self) -> int:
        return len(self.read)

    def get_one_unread(self) -> Notification | None:
        return self.unread[0] if self.unread else None

    def get_one_read(self) -> Notification | None:
        return self.read[0] if self.read else None


@pytest.fixture
def notification_factory(
    session: Session,
    sample_users: list[User],
    published_post: Post,
) -> Callable[..., CreatedNotifications]:
    """
    通知数据工厂 fixture，用于按需创建灵活的通知测试数据。

    返回一个函数，该函数接受一个规格列表 (specs)，每个规格定义了一批要创建的通知。

    工厂函数签名:
        _factory(specs: list[dict], recipient: User | None = None)
        -> CreatedNotifications

    规格 (spec) 字典支持的键:
        - count (int): 创建通知的数量 (默认为 1)
        - is_read (bool): 是否已读 (默认为 False)
        - minutes_ago (int): 创建于多少分钟前 (用于控制时间)
        - notification_type (NotificationType): 通知类型 (默认为 LIKE)
        - actor_index (int): 使用 sample_users 中的哪个用户作为 actor (默认为 1)
        - aggregated_count (int): 聚合数量 (默认为 1)

    返回:
        CreatedNotifications: 一个包含已创建通知列表和统计信息的数据对象。

    Example:
        def test_example(notification_factory):
            # 创建 3 条 5 分钟前未读的点赞通知
            data = notification_factory([
                {
                    "count": 3,
                    "is_read": False,
                    "minutes_ago": 5,
                    "notification_type": NotificationType.LIKE,
                }
            ])
            assert data.unread_count == 3

            # 创建 1 条已读的关注通知
            follow_data = notification_factory(
                [{"is_read": True, "notification_type": NotificationType.FOLLOW}])
            assert follow_data.read_count == 1
    """
    from app.models.notification import Notification, NotificationType

    def _factory(
        specs: list[dict], recipient: User | None = None
    ) -> CreatedNotifications:
        """根据规格列表创建通知"""
        created_notifications = []
        now = datetime.now(UTC)
        _recipient = recipient or sample_users[0]

        for spec in specs:
            count = spec.get("count", 1)
            is_read = spec.get("is_read", False)
            minutes_ago = spec.get("minutes_ago")
            notification_type = spec.get("notification_type", NotificationType.LIKE)
            actor_index = spec.get("actor_index", 1)
            aggregated_count = spec.get("aggregated_count", 1)

            actor = sample_users[actor_index]

            for _ in range(count):
                created_at = (
                    (now - timedelta(minutes=minutes_ago)) if minutes_ago else now
                )
                read_at = created_at + timedelta(minutes=1) if is_read else None

                notification = Notification(
                    recipient_id=_recipient.id,
                    actor_id=actor.id,
                    notification_type=notification_type,
                    post_id=published_post.id,
                    aggregated_count=aggregated_count,
                    is_read=is_read,
                    created_at=created_at,
                    read_at=read_at,
                )
                created_notifications.append(notification)

        session.add_all(created_notifications)
        session.commit()

        for notif in created_notifications:
            session.refresh(notif)

        read_items = [n for n in created_notifications if n.is_read]
        unread_items = [n for n in created_notifications if not n.is_read]

        return CreatedNotifications(
            all=created_notifications,
            read=read_items,
            unread=unread_items,
        )

    return _factory


# ============================================
# 端到端测试数据 Fixture
# ============================================


@dataclass(slots=True)
class E2ENotificationData:
    """端到端测试数据容器

    用于端到端测试，提供清晰的用户角色和完整的认证信息。
    所有操作通过真实 API 调用完成，验证事件驱动的通知创建和聚合。
    """

    author: User  # 文章作者（接收通知的人）
    user_a: User  # 用户 A（操作者）
    user_b: User  # 用户 B（操作者）
    post: Post  # 已发布的文章
    author_headers: dict[str, str]  # 作者的认证 headers
    user_a_headers: dict[str, str]  # 用户 A 的认证 headers
    user_b_headers: dict[str, str]  # 用户 B 的认证 headers


@pytest.fixture
def e2e_notification_data(
    session: Session,
    sample_users: list[User],
    published_post: Post,
) -> E2ENotificationData:
    """端到端测试数据工厂

    设置：
    - author = sample_users[0] (文章作者，published_post 的作者)
    - user_a = sample_users[1] (zhangsan，执行操作的用户)
    - user_b = sample_users[2] (lisi，执行操作的用户)
    - post = published_post

    特点：
    - 所有操作通过 API 调用完成（点赞、评论、关注）
    - 验证事件驱动的通知创建和聚合
    - 不预设任何通知数据（从零开始）
    - 提供所有用户的认证 headers，方便测试使用

    Returns:
        E2ENotificationData: 包含所有测试所需数据的容器对象
    """
    author = sample_users[0]
    user_a = sample_users[1]
    user_b = sample_users[2]

    author_token = create_access_token(data={"sub": str(author.id)})
    user_a_token = create_access_token(data={"sub": str(user_a.id)})
    user_b_token = create_access_token(data={"sub": str(user_b.id)})

    return E2ENotificationData(
        author=author,
        user_a=user_a,
        user_b=user_b,
        post=published_post,
        author_headers={"Authorization": f"Bearer {author_token}"},
        user_a_headers={"Authorization": f"Bearer {user_a_token}"},
        user_b_headers={"Authorization": f"Bearer {user_b_token}"},
    )
