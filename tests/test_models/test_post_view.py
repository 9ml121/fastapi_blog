"""
PostView 模型测试套件

测试覆盖：
1. 基础 CRUD 操作
2. 数据库约束（外键、NOT NULL）
3. 模型关系（User-PostView, Post-PostView）
4. 匿名浏览支持
5. 防刷功能（is_duplicate）
6. 级联删除行为
7. 属性方法（is_anonymous）
8. 边界情况（IP地址、User-Agent等）
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.post_view import PostView
from app.models.user import User


class TestPostViewModel:
    """PostView 模型测试类"""

    # ============ 基础 CRUD 操作测试 ============

    def test_create_post_view(self, session: Session, sample_user: User, sample_post: Post):
        """测试创建浏览记录"""
        view = PostView(
            user_id=sample_user.id,
            post_id=sample_post.id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        session.add(view)
        session.commit()
        session.refresh(view)

        assert view.id is not None
        assert view.user_id == sample_user.id
        assert view.post_id == sample_post.id
        assert view.ip_address == "192.168.1.1"
        assert view.user_agent == "Mozilla/5.0"
        assert isinstance(view.viewed_at, datetime)

    def test_create_anonymous_view(self, session: Session, sample_post: Post):
        """测试创建匿名浏览记录"""
        view = PostView(
            user_id=None,  # 匿名用户
            post_id=sample_post.id,
        )
        session.add(view)
        session.commit()
        session.refresh(view)

        assert view.id is not None
        assert view.user_id is None
        assert view.post_id == sample_post.id

    def test_read_post_view(self, session: Session, sample_user: User, sample_post: Post):
        """测试查询浏览记录"""
        view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()

        # 通过 ID 查询
        retrieved_view = session.query(PostView).filter_by(id=view.id).first()
        assert retrieved_view is not None
        assert retrieved_view.user_id == sample_user.id

    def test_delete_post_view(self, session: Session, sample_user: User, sample_post: Post):
        """测试删除浏览记录"""
        view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()
        view_id = view.id

        # 硬删除
        session.delete(view)
        session.commit()

        # 验证已删除
        deleted_view = session.query(PostView).filter_by(id=view_id).first()
        assert deleted_view is None

    # ============ 数据库约束测试 ============

    def test_post_id_required(self, session: Session, sample_user: User):
        """测试 post_id 不能为空"""
        with pytest.raises(IntegrityError):
            view = PostView(user_id=sample_user.id, post_id=None)
            session.add(view)
            session.commit()

    def test_invalid_user_foreign_key(self, session: Session, sample_post: Post):
        """测试无效的用户外键"""
        import uuid

        with pytest.raises(IntegrityError):
            view = PostView(
                user_id=uuid.uuid4(),  # 不存在的用户
                post_id=sample_post.id,
            )
            session.add(view)
            session.commit()

    def test_invalid_post_foreign_key(self, session: Session, sample_user: User):
        """测试无效的文章外键"""
        import uuid

        with pytest.raises(IntegrityError):
            view = PostView(
                user_id=sample_user.id,
                post_id=uuid.uuid4(),  # 不存在的文章
            )
            session.add(view)
            session.commit()

    # ============ 模型关系测试 ============

    def test_post_view_user_relationship(self, session: Session, sample_user: User, sample_post: Post):
        """测试 PostView -> User 关系"""
        view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()
        session.refresh(view)

        # 验证关系
        assert view.user is not None
        assert view.user.id == sample_user.id
        assert view.user.username == sample_user.username

    def test_post_view_post_relationship(self, session: Session, sample_user: User, sample_post: Post):
        """测试 PostView -> Post 关系"""
        view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()
        session.refresh(view)

        # 验证关系
        assert view.post is not None
        assert view.post.id == sample_post.id
        assert view.post.title == sample_post.title

    def test_user_post_views_relationship(self, session: Session, sample_user: User, sample_post_data):
        """测试 User -> PostView 关系（一对多）"""
        # 创建3篇文章
        post1 = Post(**sample_post_data())
        post2 = Post(**sample_post_data())
        post3 = Post(**sample_post_data())
        session.add_all([post1, post2, post3])
        session.commit()

        # 用户浏览这3篇文章
        view1 = PostView(user_id=sample_user.id, post_id=post1.id)
        view2 = PostView(user_id=sample_user.id, post_id=post2.id)
        view3 = PostView(user_id=sample_user.id, post_id=post3.id)
        session.add_all([view1, view2, view3])
        session.commit()

        # 验证用户的浏览历史
        session.refresh(sample_user)
        assert len(sample_user.post_views) == 3
        assert view1 in sample_user.post_views
        assert view2 in sample_user.post_views
        assert view3 in sample_user.post_views

    def test_post_post_views_relationship(self, session: Session, sample_user_data, sample_post: Post):
        """测试 Post -> PostView 关系（一对多）"""
        # 创建3个用户
        user1 = User(**sample_user_data())
        user2 = User(**sample_user_data())
        user3 = User(**sample_user_data())
        session.add_all([user1, user2, user3])
        session.commit()

        # 3个用户浏览同一篇文章
        view1 = PostView(user_id=user1.id, post_id=sample_post.id)
        view2 = PostView(user_id=user2.id, post_id=sample_post.id)
        view3 = PostView(user_id=user3.id, post_id=sample_post.id)
        session.add_all([view1, view2, view3])
        session.commit()

        # 验证文章的浏览记录
        session.refresh(sample_post)
        assert len(sample_post.post_views) == 3
        assert view1 in sample_post.post_views
        assert view2 in sample_post.post_views
        assert view3 in sample_post.post_views

    # ============ 匿名浏览测试 ============

    def test_anonymous_view_user_relationship(self, session: Session, sample_post: Post):
        """测试匿名浏览记录的 user 关系"""
        view = PostView(user_id=None, post_id=sample_post.id)
        session.add(view)
        session.commit()
        session.refresh(view)

        # 验证匿名浏览没有关联用户
        assert view.user is None
        assert view.user_id is None

    def test_mixed_authenticated_and_anonymous_views(self, session: Session, sample_user: User, sample_post: Post):
        """测试同时存在已登录和匿名浏览记录"""
        # 已登录用户浏览
        auth_view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        # 匿名用户浏览
        anon_view = PostView(user_id=None, post_id=sample_post.id)

        session.add_all([auth_view, anon_view])
        session.commit()

        # 验证文章有2条浏览记录
        session.refresh(sample_post)
        assert len(sample_post.post_views) == 2

        # 验证用户只有1条浏览记录（不包含匿名）
        session.refresh(sample_user)
        assert len(sample_user.post_views) == 1

    # ============ 级联删除测试 ============

    def test_delete_post_cascades_to_views(self, session: Session, sample_user: User, sample_post_data):
        """测试删除文章时级联删除浏览记录"""
        post = Post(**sample_post_data())
        session.add(post)
        session.commit()

        # 创建浏览记录
        view = PostView(user_id=sample_user.id, post_id=post.id)
        session.add(view)
        session.commit()
        view_id = view.id

        # 删除文章
        session.delete(post)
        session.commit()

        # 验证浏览记录被级联删除
        deleted_view = session.query(PostView).filter_by(id=view_id).first()
        assert deleted_view is None

    def test_delete_user_cascades_to_views(self, session: Session, sample_user_data, sample_post: Post):
        """测试删除用户时级联删除浏览记录"""
        user = User(**sample_user_data())
        session.add(user)
        session.commit()

        # 创建浏览记录
        view = PostView(user_id=user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()
        view_id = view.id

        # 删除用户
        session.delete(user)
        session.commit()

        # 验证浏览记录被级联删除
        deleted_view = session.query(PostView).filter_by(id=view_id).first()
        assert deleted_view is None

    # ============ 业务方法测试 ============

    def test_is_duplicate_authenticated_user(self, session: Session, sample_user: User, sample_post: Post):
        """测试防刷功能（已登录用户）"""
        # 第一次浏览
        view1 = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view1)
        session.commit()

        # 5分钟内再次浏览，应该被识别为重复
        is_dup = PostView.is_duplicate(session, sample_user.id, sample_post.id)
        assert is_dup is True

        # 模拟6分钟后再次浏览
        view1.viewed_at = datetime.now(UTC) - timedelta(minutes=6)
        session.commit()
        is_dup_later = PostView.is_duplicate(session, sample_user.id, sample_post.id)
        assert is_dup_later is False  # 6分钟前不算重复

    def test_is_duplicate_anonymous_user(self, session: Session, sample_post: Post):
        """测试防刷功能（匿名用户）"""
        # 匿名用户第一次浏览
        view = PostView(user_id=None, post_id=sample_post.id)
        session.add(view)
        session.commit()

        # 匿名用户无法准确判断重复，返回 False
        is_dup = PostView.is_duplicate(session, None, sample_post.id)
        assert is_dup is False

        # 模拟6分钟后再次浏览, 还是返回 False
        view.viewed_at = datetime.now(UTC) - timedelta(minutes=6)
        session.commit()
        is_dup_later = PostView.is_duplicate(session, None, sample_post.id)
        assert is_dup_later is False

    def test_is_duplicate_different_posts(self, session: Session, sample_user: User, sample_post_data):
        """测试不同文章不算重复"""
        post1 = Post(**sample_post_data())
        post2 = Post(**sample_post_data())
        session.add_all([post1, post2])
        session.commit()

        # 浏览文章1
        view1 = PostView(user_id=sample_user.id, post_id=post1.id)
        session.add(view1)
        session.commit()

        # 浏览文章2，不算重复
        is_dup = PostView.is_duplicate(session, sample_user.id, post2.id)
        assert is_dup is False

    # ============ 属性方法测试 ============

    def test_is_anonymous_property(self, session: Session, sample_user: User, sample_post: Post):
        """测试 is_anonymous 属性"""
        # 已登录用户浏览
        auth_view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        assert auth_view.is_anonymous is False

        # 匿名用户浏览
        anon_view = PostView(user_id=None, post_id=sample_post.id)
        assert anon_view.is_anonymous is True

    # ============ 字符串表示测试 ============

    def test_post_view_repr(self, session: Session, sample_user: User, sample_post: Post):
        """测试 __repr__ 方法"""
        view = PostView(user_id=sample_user.id, post_id=sample_post.id)
        session.add(view)
        session.commit()
        session.refresh(view)

        repr_str = repr(view)
        assert "PostView" in repr_str
        assert str(view.id) in repr_str
        assert str(view.user_id) in repr_str

    def test_anonymous_view_repr(self, session: Session, sample_post: Post):
        """测试匿名浏览的 __repr__ 方法"""
        view = PostView(user_id=None, post_id=sample_post.id)
        session.add(view)
        session.commit()
        session.refresh(view)

        repr_str = repr(view)
        assert "PostView" in repr_str
        assert "anonymous" in repr_str

    # ============ 边界情况测试 ============

    def test_ipv6_address(self, session: Session, sample_user: User, sample_post: Post):
        """测试 IPv6 地址存储"""
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        view = PostView(
            user_id=sample_user.id,
            post_id=sample_post.id,
            ip_address=ipv6,
        )
        session.add(view)
        session.commit()

        assert view.ip_address == ipv6
        assert len(view.ip_address) <= 45  # 字段长度限制

    def test_very_long_user_agent(self, session: Session, sample_user: User, sample_post: Post):
        """测试超长 User-Agent"""
        long_ua = "A" * 500  # 正好 500 字符（字段限制）
        view = PostView(
            user_id=sample_user.id,
            post_id=sample_post.id,
            user_agent=long_ua,
        )
        session.add(view)
        session.commit()

        assert view.user_agent is not None
        assert len(view.user_agent) == 500

    def test_optional_fields_can_be_null(self, session: Session, sample_user: User, sample_post: Post):
        """测试可选字段可以为空"""
        view = PostView(
            user_id=sample_user.id,
            post_id=sample_post.id,
            # ip_address 和 user_agent 不提供
        )
        session.add(view)
        session.commit()

        assert view.ip_address is None
        assert view.user_agent is None
