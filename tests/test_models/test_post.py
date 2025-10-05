"""
Post 模型测试

测试 Post 模型的字段定义、约束、关系、方法等功能
"""

import logging
import uuid
from datetime import datetime

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from app.db.database import Base
from app.models.post import Post, PostStatus
from app.models.user import User

# 配置测试日志
logger = logging.getLogger(__name__)


class TestPostModel:
    """Post 模型测试类"""

    @pytest.fixture(scope="class")
    def engine(self):
        """创建测试数据库引擎"""
        # ①创建 sqlite 内存数据库引擎
        engine = create_engine("sqlite:///:memory:", echo=False)

        # ②启用 SQLite 外键约束（默认是关闭的）
        import sqlite3

        from sqlalchemy import event
        from sqlalchemy.pool import ConnectionPoolEntry

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn: sqlite3.Connection, _connection_record: ConnectionPoolEntry) -> None:
            """每次建立连接时自动启用外键约束

            Args:
                dbapi_conn: 原始数据库连接对象
                _connection_record: SQLAlchemy 连接池记录（未使用，但签名要求必须接收）
            """
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # ③ 创建表（此时会建立第一个连接，触发事件）
        Base.metadata.create_all(engine)

        yield engine

        # 清理资源
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    @pytest.fixture
    def session(self, engine: Engine):
        """创建测试数据库会话"""
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def sample_user(self, session: Session):
        """创建测试用户"""
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f"author_{unique_id}",
            email=f"author_{unique_id}@example.com",
            password_hash="hashed_password_123",
            nickname=f"作者_{unique_id}",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def sample_post_data(self):
        """示例文章数据 - 每次生成唯一数据"""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "title": f"测试文章标题_{unique_id}",
            "content": f"这是一篇测试文章的内容，用于验证 Post 模型的功能。唯一标识：{unique_id}",
            "summary": f"这是文章摘要_{unique_id}",
            "slug": f"test-post-{unique_id}",
        }

    def test_post_creation(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        post = Post(author_id=sample_user.id, **sample_post_data)

        session.add(post)
        session.commit()
        session.refresh(post)

        # 验证基本字段
        assert post.id is not None
        assert isinstance(post.id, uuid.UUID)
        assert post.title == sample_post_data["title"]
        assert post.content == sample_post_data["content"]
        assert post.summary == sample_post_data["summary"]
        assert post.slug == sample_post_data["slug"]
        assert post.author_id == sample_user.id

        # 验证默认值
        assert post.status == PostStatus.DRAFT
        assert post.is_featured is False
        assert post.view_count == 0
        assert post.published_at is None

        # 验证时间戳
        assert post.created_at is not None
        assert post.updated_at is not None
        assert isinstance(post.created_at, datetime)
        assert isinstance(post.updated_at, datetime)

    def test_post_status_enum(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试文章状态枚举"""
        post = Post(author_id=sample_user.id, **sample_post_data)

        session.add(post)
        session.commit()
        session.refresh(post)

        # 测试默认状态
        assert post.status == PostStatus.DRAFT
        assert post.is_draft is True
        assert post.is_published is False
        assert post.is_archived is False

        # 测试状态变更
        post.status = PostStatus.PUBLISHED
        assert post.is_draft is False
        assert post.is_published is True
        assert post.is_archived is False

        post.status = PostStatus.ARCHIVED
        assert post.is_draft is False
        assert post.is_published is False
        assert post.is_archived is True

    def test_slug_unique_constraint(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试 slug 唯一性约束"""
        # 创建第一篇文章
        post1 = Post(author_id=sample_user.id, **sample_post_data)
        session.add(post1)
        session.commit()

        # 尝试创建相同 slug 的文章
        post2_data = sample_post_data.copy()
        post2_data["title"] = "不同的标题"
        post2 = Post(
            author_id=sample_user.id,
            **post2_data,  # 相同的 slug
        )
        session.add(post2)

        # 应该抛出完整性错误
        with pytest.raises(IntegrityError):
            session.commit()

    def test_author_relationship(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试与用户的关联关系"""
        post = Post(author_id=sample_user.id, **sample_post_data)
        session.add(post)
        session.commit()
        session.refresh(post)

        # 测试正向关系（Post -> User）
        assert post.author is not None
        assert post.author.id == sample_user.id
        assert post.author.username == sample_user.username

        # 测试反向关系（User -> Post）
        assert len(sample_user.posts) >= 1
        assert post in sample_user.posts

    def test_post_business_methods(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试文章业务方法"""
        post = Post(author_id=sample_user.id, **sample_post_data)
        session.add(post)
        session.commit()

        # 测试发布方法
        assert post.status == PostStatus.DRAFT
        assert post.published_at is None

        post.publish()
        assert post.status == PostStatus.PUBLISHED
        assert post.published_at is not None
        assert isinstance(post.published_at, datetime)

        # 测试归档方法
        post.archive()
        assert post.status == PostStatus.ARCHIVED

        # 测试恢复草稿方法
        post.revert_to_draft()
        assert post.status == PostStatus.DRAFT
        assert post.published_at is None

        # 测试置顶切换
        assert post.is_featured is False
        post.toggle_featured()
        assert post.is_featured is True
        post.toggle_featured()
        assert post.is_featured is False

        # 测试浏览量增加
        initial_count = post.view_count
        post.increment_view_count()
        assert post.view_count == initial_count + 1

    def test_post_properties(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试文章计算属性"""
        post = Post(author_id=sample_user.id, **sample_post_data)

        session.add(post)
        session.commit()
        session.refresh(post)

        # 测试显示标题
        assert post.display_title == f"[草稿] {sample_post_data['title']}"

        post.status = PostStatus.PUBLISHED
        assert post.display_title == sample_post_data["title"]

        post.status = PostStatus.ARCHIVED
        assert post.display_title == f"[归档] {sample_post_data['title']}"

        # 测试字数统计（简单实现）
        word_count = post.word_count
        assert isinstance(word_count, int)
        assert word_count > 0

        # 测试阅读时间
        reading_time = post.reading_time
        assert isinstance(reading_time, int)
        assert reading_time >= 1

    def test_post_string_representations(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试文章字符串表示"""
        post = Post(author_id=sample_user.id, **sample_post_data)
        session.add(post)
        session.commit()
        session.refresh(post)

        # 测试 __str__ 方法
        assert str(post) == sample_post_data["title"]

        # 测试 __repr__ 方法
        repr_str = repr(post)
        assert "Post" in repr_str
        assert str(post.id) in repr_str
        assert sample_post_data["title"][:30] in repr_str
        assert "draft" in repr_str.lower()

    def test_post_cascade_delete(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试级联删除"""
        post = Post(author_id=sample_user.id, **sample_post_data)
        session.add(post)
        session.commit()
        post_id = post.id

        # 删除用户，文章应该被级联删除
        session.delete(sample_user)
        session.commit()

        # 验证文章已被删除
        deleted_post = session.query(Post).filter(Post.id == post_id).first()
        assert deleted_post is None

    def test_slug_generation(self, session: Session, sample_user: User):
        """测试 slug 生成方法 - 实例方法"""
        post = Post(author_id=sample_user.id, title="我的文章标题", content="测试内容", slug="temp")

        # 1. 不传参数，使用 self.title
        generated_slug = post.generate_slug()
        assert generated_slug == "我的文章标题"

        # 2. 传入指定标题
        generated_slug = post.generate_slug("Hello World! Test 123")
        assert generated_slug == "Hello-World-Test-123"

        # 3. 传入 None，应该使用 self.title
        generated_slug = post.generate_slug(None)
        assert generated_slug == "我的文章标题"

        # 4. 传入空字符串，应该 fallback 到 self.title（因为 "" 是 falsy）
        generated_slug = post.generate_slug("")
        assert generated_slug == "我的文章标题"

        # 5. 传入中文标题
        generated_slug = post.generate_slug("Python Web开发实战")
        assert generated_slug == "Python-Web开发实战"

        # 6. 传入带特殊字符的标题
        generated_slug = post.generate_slug("文章#标题@特殊字符!")
        assert generated_slug == "文章标题特殊字符"

    def test_slug_static_method(self):
        """测试 slug 生成的静态方法 - 核心逻辑"""
        # 1. 正常英文标题
        slug = Post._generate_slug_from_title("Hello World Test")
        assert slug == "Hello-World-Test"

        # 2. 正常中文标题
        slug = Post._generate_slug_from_title("如何学习FastAPI框架")
        assert slug == "如何学习FastAPI框架"

        # 3. 中英文混合
        slug = Post._generate_slug_from_title("Python Web开发实战")
        assert slug == "Python-Web开发实战"

        # 4. 特殊字符处理
        slug = Post._generate_slug_from_title("Vue3 + React对比分析!!!")
        assert slug == "Vue3-React对比分析"

        # 5. 空字符串 - 应该生成时间戳格式
        slug = Post._generate_slug_from_title("")
        assert slug.startswith("文章-")
        assert len(slug) == 18  # "文章-20251001-143022"

        # 6. 全是特殊字符 - 应该生成时间戳格式
        slug = Post._generate_slug_from_title("@#$%^&*()")
        assert slug.startswith("文章-")
        assert len(slug) == 18

        # 7. 多个空格和连字符
        slug = Post._generate_slug_from_title("Hello    World---Test")
        assert slug == "Hello-World-Test"

        # 8a. 超长标题（带连字符）- 应该在连字符处智能截断
        long_title_with_dash = "这是第一部分-这是第二部分-这是第三部分-这是第四部分-这是第五部分-这是第六部分"
        slug = Post._generate_slug_from_title(long_title_with_dash)
        logger.debug(f"超长标题（带连字符）生成的 slug: {slug}")
        assert len(slug) <= 20
        assert not slug.endswith("...")  # 在连字符处截断，不加省略号
        assert slug.count("-") >= 1  # 应该保留至少一个连字符
        assert slug.endswith("部分")  # 应该在完整的词组处结束

        # 8b. 超长标题（无连字符）- 应该直接截断并加省略号
        long_title_no_dash = "这是一个非常非常非常非常非常非常非常非常非常非常长的标题没有连字符"
        slug = Post._generate_slug_from_title(long_title_no_dash)
        logger.debug(f"超长标题（无连字符）生成的 slug: {slug}")
        assert len(slug) <= 20
        assert slug.endswith("...")  # 无连字符，加省略号

        # 9. 首尾有空格和连字符
        slug = Post._generate_slug_from_title("  -Hello World-  ")
        assert slug == "Hello-World"

    def test_summary_auto_generation(self, session: Session, sample_user: User):
        """测试摘要自动生成"""
        long_content = "这是一篇很长的文章内容。" * 50  # 创建长内容
        post = Post(author_id=sample_user.id, title="测试文章", content=long_content, slug="test-summary")

        # 测试自动生成摘要
        post.set_summary_from_content(max_length=100)
        logger.debug(f"长文章自动生成的摘要: {post.summary}")
        assert post.summary is not None
        assert len(post.summary) <= 103  # 100 + "..."
        assert post.summary.endswith("...")

        # 测试短内容
        short_content = "这是短内容"
        post.content = short_content
        post.set_summary_from_content(max_length=100)
        assert post.summary == short_content

    def test_post_required_fields(self, session: Session, sample_user: User):
        """测试必需字段约束"""
        # 测试缺少标题
        with pytest.raises(IntegrityError):
            post = Post(
                author_id=sample_user.id,
                content="内容",
                slug="test-slug",
                # 缺少 title
            )
            session.add(post)
            session.commit()

    def test_post_optional_fields(self, session: Session, sample_user: User, sample_post_data: dict[str, str]):
        """测试可选字段"""
        # 不提供可选字段
        post_data = sample_post_data.copy()
        del post_data["summary"]  # 移除可选的摘要字段

        post = Post(author_id=sample_user.id, **post_data)
        session.add(post)
        session.commit()
        session.refresh(post)

        # 验证可选字段为 None
        assert post.summary is None
        assert post.published_at is None

    def test_foreign_key_constraint(self, session: Session, sample_post_data: dict[str, str]):
        """测试外键约束"""
        # 使用不存在的 author_id
        logger.debug("测试外键约束：使用不存在的 author_id")
        fake_uuid = uuid.uuid4()
        post = Post(author_id=fake_uuid, **sample_post_data)

        session.add(post)

        # 应该抛出完整性错误
        with pytest.raises(IntegrityError):
            session.commit()
