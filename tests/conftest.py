"""
Pytest 配置文件 - 定义共享的 fixture

这个文件中的 fixture 会自动对所有测试文件可用，无需显式 import。
"""

import sqlite3
import uuid
from collections.abc import Callable, Generator

import pytest
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.db.database import Base
from app.models.post import Post
from app.models.user import User

# ============================================
# 数据库相关 Fixture
# ============================================


@pytest.fixture(scope="function")
def engine() -> Generator[Engine, None, None]:
    """创建测试数据库引擎（内存 SQLite 数据库）

    配置：
    - 使用内存数据库，速度快，测试隔离
    - 自动启用 SQLite 外键约束（默认关闭）
    - 每个测试函数独立的数据库实例

    Returns:
        Engine: SQLAlchemy 数据库引擎
    """
    # 创建内存数据库引擎，并允许跨线程使用
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 启用 SQLite 外键约束（必须在 create_all() 之前）
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn: sqlite3.Connection, _connection_record: ConnectionPoolEntry) -> None:
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
# 辅助 Fixture
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
