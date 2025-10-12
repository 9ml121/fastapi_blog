"""
Comment 模型测试套件

测试覆盖：
1. 基础 CRUD 操作
2. 数据库约束（外键、唯一性等）
3. 模型关系（User-Comment, Post-Comment, Comment-Comment）
4. 业务方法（审核、软删除、恢复）
5. 属性方法（is_top_level, reply_count）
6. 边界情况（空内容、层级删除等）
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User


class TestCommentModel:
    """Comment 模型测试类"""

    # ============ 基础 CRUD 操作测试 ============

    def test_create_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试创建评论"""
        comment = Comment(
            content="This is a test comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        assert comment.id is not None
        assert comment.content == "This is a test comment."
        assert comment.user_id == sample_user.id
        assert comment.post_id == sample_post.id
        assert comment.parent_id is None  # 顶级评论
        assert comment.is_approved is False  # 默认未审核
        assert comment.is_deleted is False  # 默认未删除
        assert isinstance(comment.created_at, datetime)
        assert isinstance(comment.updated_at, datetime)

    def test_read_comment(self, session: Session, sample_user: User, sample_post: Post):
        """测试查询评论"""
        comment = Comment(
            content="Test comment for reading.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        # 通过 ID 查询
        retrieved_comment = session.query(Comment).filter_by(id=comment.id).first()
        assert retrieved_comment is not None
        assert retrieved_comment.content == "Test comment for reading."
        assert retrieved_comment.user_id == sample_user.id

    def test_update_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试更新评论"""
        comment = Comment(
            content="Original content.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        # 更新内容
        comment.content = "Updated content."
        session.commit()
        session.refresh(comment)

        assert comment.content == "Updated content."

    def test_delete_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试删除评论（硬删除）"""
        comment = Comment(
            content="Comment to be deleted.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        comment_id = comment.id

        # 硬删除
        session.delete(comment)
        session.commit()

        # 验证已删除
        deleted_comment = session.query(Comment).filter_by(id=comment_id).first()
        assert deleted_comment is None

    # ============ 数据库约束测试 ============

    def test_comment_content_not_null(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试评论内容不能为空"""
        with pytest.raises(IntegrityError):
            comment = Comment(
                content=None,  # 违反 NOT NULL 约束
                user_id=sample_user.id,
                post_id=sample_post.id,
            )
            session.add(comment)
            session.commit()

    def test_comment_requires_user_id(self, session: Session, sample_post: Post):
        """测试评论必须关联用户"""
        with pytest.raises(IntegrityError):
            comment = Comment(
                content="Comment without user.",
                user_id=None,  # 违反 NOT NULL 约束
                post_id=sample_post.id,
            )
            session.add(comment)
            session.commit()

    def test_comment_requires_post_id(self, session: Session, sample_user: User):
        """测试评论必须关联文章"""
        with pytest.raises(IntegrityError):
            comment = Comment(
                content="Comment without post.",
                user_id=sample_user.id,
                post_id=None,  # 违反 NOT NULL 约束
            )
            session.add(comment)
            session.commit()

    def test_comment_foreign_key_user(self, session: Session, sample_post: Post):
        """测试评论的用户外键约束"""
        with pytest.raises(IntegrityError):
            comment = Comment(
                content="Comment with invalid user.",
                user_id=uuid.uuid4(),  # 不存在的用户 ID
                post_id=sample_post.id,
            )
            session.add(comment)
            session.commit()

    def test_comment_foreign_key_post(self, session: Session, sample_user: User):
        """测试评论的文章外键约束"""
        with pytest.raises(IntegrityError):
            comment = Comment(
                content="Comment with invalid post.",
                user_id=sample_user.id,
                post_id=uuid.uuid4(),  # 不存在的文章 ID
            )
            session.add(comment)
            session.commit()

    # ============ 模型关系测试 ============

    def test_comment_author_relationship(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 Comment -> User 关系"""
        comment = Comment(
            content="Test comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        # 验证关系
        assert comment.author is not None
        assert comment.author.id == sample_user.id
        assert comment.author.username == sample_user.username

    def test_user_comments_relationship(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 User -> Comment 关系（一对多）"""
        # 创建多条评论
        comment1 = Comment(
            content="First comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        comment2 = Comment(
            content="Second comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add_all([comment1, comment2])
        session.commit()
        session.refresh(sample_user)

        # 验证用户的评论列表
        assert len(sample_user.comments) == 2
        assert comment1 in sample_user.comments
        assert comment2 in sample_user.comments

    def test_comment_post_relationship(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 Comment -> Post 关系"""
        comment = Comment(
            content="Test comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        # 验证关系
        assert comment.post is not None
        assert comment.post.id == sample_post.id
        assert comment.post.title == sample_post.title

    def test_post_comments_relationship(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 Post -> Comment 关系（一对多）"""
        # 1. 创建 3 条评论关联到 sample_post
        comment1 = Comment(
            content="First comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        comment2 = Comment(
            content="Second comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        comment3 = Comment(
            content="Third comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add_all([comment1, comment2, comment3])
        session.commit()

        # 2. session.refresh(sample_post) 刷新文章对象
        session.refresh(sample_post)

        # 3. 验证 len(sample_post.comments) == 3
        assert len(sample_post.comments) == 3

        # 4. 验证评论是否按 created_at 排序（Post 模型中设置了 order_by）
        assert sample_post.comments[0].content == "First comment."
        assert sample_post.comments[1].content == "Second comment."
        assert sample_post.comments[2].content == "Third comment."

    # ============ 自引用关系测试（评论回复评论）============

    def test_create_reply_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试创建回复评论（父子关系）"""
        # 1. 创建顶级评论（parent_id=None）
        top_comment = Comment(
            content="Top comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(top_comment)
        session.commit()

        # 2. 创建回复评论（parent_id=顶级评论.id）
        reply_comment = Comment(
            content="Reply comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=top_comment.id,
        )
        session.add(reply_comment)
        session.commit()

        # 3. 验证回复评论的 parent_id 正确
        assert reply_comment.parent_id == top_comment.id

        # 4. 验证回复评论的 parent 关系指向顶级评论
        assert reply_comment.parent == top_comment

    def test_comment_replies_relationship(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试评论的 replies 关系（一对多）"""
        # 1. 创建 1 条顶级评论
        top_comment = Comment(
            content="Top comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(top_comment)
        session.commit()

        # 2. 创建 3 条回复评论都指向顶级评论
        reply_comment1 = Comment(
            content="Reply comment1.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=top_comment.id,
        )
        reply_comment2 = Comment(
            content="Reply comment2.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=top_comment.id,
        )
        reply_comment3 = Comment(
            content="Reply comment3.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=top_comment.id,
        )
        session.add_all([reply_comment1, reply_comment2, reply_comment3])
        session.commit()

        # 3. session.refresh(顶级评论)
        session.refresh(top_comment)

        # 4. 验证 len(顶级评论.replies) == 3
        assert len(top_comment.replies) == 3
        # 5. 验证所有回复的 parent_id 都是顶级评论的 id
        assert reply_comment1.parent_id == top_comment.id
        assert reply_comment2.parent_id == top_comment.id
        assert reply_comment3.parent_id == top_comment.id

    def test_nested_comment_structure(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试多层嵌套评论结构"""
        # 创建评论层级：评论1 -> 评论2 -> 评论3
        comment1 = Comment(
            content="Top level comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment1)
        session.commit()
        session.refresh(comment1)

        comment2 = Comment(
            content="Reply to comment 1.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment1.id,
        )
        session.add(comment2)
        session.commit()
        session.refresh(comment2)

        comment3 = Comment(
            content="Reply to comment 2.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment2.id,
        )
        session.add(comment3)
        session.commit()

        session.refresh(comment1)
        session.refresh(comment2)

        # 验证层级结构
        assert len(comment1.replies) == 1
        assert comment1.replies[0].id == comment2.id
        assert len(comment2.replies) == 1
        assert comment2.replies[0].id == comment3.id
        assert comment3.parent is not None
        assert comment3.parent.id == comment2.id
        assert comment2.parent is not None
        assert comment2.parent.id == comment1.id

    def test_delete_parent_cascades_to_replies(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试删除父评论时级联删除子评论"""
        # 1. 创建 1 条顶级评论
        comment1 = Comment(
            content="Top level comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment1)
        session.commit()

        # 2. 创建 2 条回复评论
        comment2 = Comment(
            content="Reply to comment 1.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment1.id,
        )
        session.add(comment2)
        session.commit()
        session.refresh(comment2)

        comment3 = Comment(
            content="Reply to comment 2.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment2.id,
        )
        session.add(comment3)
        session.commit()

        session.refresh(comment1)
        session.refresh(comment2)

        # 3. 记录所有评论的 ID
        all_comments_id = [comment1.id, comment2.id, comment3.id]
        # 4. 删除顶级评论：session.delete(顶级评论)
        session.delete(comment1)
        # 5. session.commit()
        session.commit()

        # 6. 验证所有子评论也被删除了（查询应该返回 None）
        for comment_id in all_comments_id:
            deleted_comment = session.query(Comment).filter_by(id=comment_id).first()
            assert deleted_comment is None

    # ============ 业务方法测试 ============

    def test_approve_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试审核通过评论"""
        comment = Comment(
            content="Comment to be approved.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        # 初始状态
        assert comment.is_approved is False

        # 审核通过
        comment.approve()
        session.commit()
        session.refresh(comment)

        assert comment.is_approved is True

    def test_soft_delete_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试软删除评论"""
        # 1. 创建评论
        comment = Comment(
            content="Comment to be soft delete.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        # 2. 初始状态 is_deleted 应该是 False
        # 3. 调用 comment.soft_delete()
        comment.soft_delete()
        # 4. session.commit() 和 session.refresh(comment)
        session.commit()
        session.refresh(comment)

        # 5. 验证 is_deleted 变成 True
        assert comment.is_deleted is True
        # 6. 验证评论仍在数据库中（通过 ID 能查到）
        soft_deleted_comment = session.query(Comment).filter_by(id=comment.id).first()
        assert soft_deleted_comment is not None

    def test_restore_comment(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试恢复已删除的评论"""
        comment = Comment(
            content="Comment to be restored.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        # 先软删除
        comment.soft_delete()
        session.commit()
        session.refresh(comment)
        assert comment.is_deleted is True

        # 恢复
        comment.restore()
        session.commit()
        session.refresh(comment)
        assert comment.is_deleted is False

    # ============ 属性方法测试 ============

    def test_is_top_level_property(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 is_top_level 属性"""
        # 1. 创建顶级评论（parent_id=None）
        comment = Comment(
            content="Top level comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        # 2. 验证 is_top_level 返回 True
        assert comment.is_top_level is True
        # 3. 创建回复评论（parent_id=顶级评论.id）
        reply_comment = Comment(
            content="Reply comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment.id,
        )
        session.add(reply_comment)
        session.commit()
        # 4. 验证回复评论的 is_top_level 返回 False
        assert reply_comment.is_top_level is False

    def test_reply_count_property(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试 reply_count 属性"""
        # 1. 创建顶级评论
        comment = Comment(
            content="Top level comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        # 2. 初始 reply_count 应该是 0
        assert comment.reply_count == 0
        # 3. 创建 3 条回复评论
        comment1 = Comment(
            content="Reply comment 1.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment.id,
        )
        comment2 = Comment(
            content="Reply comment 2.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment.id,
        )
        comment3 = Comment(
            content="Reply comment 3.",
            user_id=sample_user.id,
            post_id=sample_post.id,
            parent_id=comment.id,
        )
        session.add_all([comment1, comment2, comment3])
        session.commit()
        # 4. session.refresh(顶级评论)
        session.refresh(comment)
        # 5. 验证 reply_count == 3
        assert comment.reply_count == 3

    # ============ 字符串表示测试 ============

    def test_comment_repr(self, session: Session, sample_user: User, sample_post: Post):
        """测试 __repr__ 方法"""
        comment = Comment(
            content="Test comment.",
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        repr_str = repr(comment)
        assert "Comment" in repr_str
        assert str(comment.id) in repr_str
        assert str(comment.user_id) in repr_str
        assert str(comment.post_id) in repr_str
        assert "is_approved=False" in repr_str

    # ============ 边界情况测试 ============

    def test_empty_content(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试空字符串内容（不应该失败）"""
        # 注意：Comment 模型的 content 字段是 nullable=False
        # 但并没有限制最小长度，所以空字符串是合法的
        comment = Comment(
            content="",  # 空字符串
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()

        assert comment.content == ""

    def test_very_long_content(
        self, session: Session, sample_user: User, sample_post: Post
    ):
        """测试超长评论内容"""
        long_content = "A" * 10000  # 10000 字符
        comment = Comment(
            content=long_content,
            user_id=sample_user.id,
            post_id=sample_post.id,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        assert len(comment.content) == 10000
        assert comment.content == long_content
