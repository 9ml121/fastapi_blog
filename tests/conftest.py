"""
Pytest 配置文件 - 定义共享的 fixture

这个文件中的 fixture 会自动对所有测试文件可用，无需显式 import。
"""

import sqlite3
import uuid
from collections.abc import Callable, Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.core.security import create_access_token
from app.crud.post import post as post_crud
from app.db.database import Base

# 导入所有模型，确保它们注册到 Base.metadata,这样 create_all() 才能创建所有表
from app.models import Comment, Post, PostView, Tag, User  # noqa: F401
from app.models.post import PostStatus
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
def sample_post(session: Session, sample_user: User) -> Post:
    """创建测试文章

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


# ============================================
# 多个用户和文章数据 Fixture
# ============================================
@pytest.fixture
def sample_users(session: Session, sample_user: User) -> list[User]:
    """创建多个测试用户，包含 sample_user

    创建 2 个额外的测试用户，用于：
    - 测试用户 API 端点
    - 作为文章和评论的作者
    - 避免与 sample_user 冲突
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
    ]

    for template in user_templates:
        user_data = UserCreate(**template)
        user = create_user(session, user_in=user_data)
        users.append(user)

    return users


@pytest.fixture
def sample_posts(session: Session, sample_user: User) -> list[Post]:
    """创建多样化的测试文章数据

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

        post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
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
