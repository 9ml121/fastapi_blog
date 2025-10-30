"""
tests/test_schemas/test_comment.py

测试 Comment Pydantic Schemas
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.user import UserSimpleResponse


class TestCommentCreateSchema:
    """测试 CommentCreate Schema"""

    def test_create_comment_success(self):
        """测试：使用有效数据成功创建"""
        comment = CommentCreate(content="This is a great post!")
        assert comment.content == "This is a great post!"
        assert comment.parent_id is None  # 默认 parent_id 为 None

    def test_create_reply_comment_success(self):
        """测试：创建一个回复（带 parent_id）应该成功"""
        parent_id = uuid4()
        comment = CommentCreate(
            content="I agree with your point.",
            parent_id=parent_id,
        )
        assert comment.content == "I agree with your point."
        assert comment.parent_id == parent_id

    def test_create_comment_with_empty_content_fails(self):
        """测试：空的 content 应该引发验证错误"""
        with pytest.raises(ValidationError):
            CommentCreate(content="")


class TestCommentResponseSchema:
    """测试 CommentResponse Schema"""

    @pytest.fixture
    def mock_author_data(self) -> dict:
        """提供一个模拟的作者数据字典"""
        return {
            "id": uuid4(),
            "username": "commenter",
            "email": "commenter@example.com",
            "nickname": "Commenter Nickname",
            "is_active": True,
            "role": "user",
            "avatar": None,
            "is_verified": True,
            "last_login": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }

    def test_create_from_orm_without_replies(self, mock_author_data: dict):
        """测试：从一个没有回复的 ORM 对象创建应该成功"""
        mock_comment_orm = type(
            "MockComment",
            (),
            {
                "id": uuid4(),
                "content": "A top-level comment",
                "created_at": "2024-01-03T10:00:00",
                "author": type("MockUser", (), mock_author_data)(),
                "replies": [],  # 没有回复
            },
        )()

        comment_response = CommentResponse.model_validate(mock_comment_orm)

        assert comment_response.content == "A top-level comment"
        assert isinstance(comment_response.author, UserSimpleResponse)
        assert comment_response.author.username == "commenter"
        assert comment_response.replies == []

    def test_create_from_orm_with_replies(self, mock_author_data: dict):
        """测试：从一个包含回复的 ORM 对象创建，应该能正确生成嵌套结构"""
        # 1. 创建一个 mock 的 "回复" 对象 (mock_reply_orm)，它没有自己的 replies。
        mock_reply_orm = type(
            "MockComment",
            (),
            {
                "id": uuid4(),
                "content": "A reply comment",
                "created_at": "2024-01-03T10:00:00",
                "author": type("MockUser", (), mock_author_data)(),
                "replies": [],  # 没有回复
            },
        )()
        # 2. 创建一个 mock 的 "父评论" 对象 (mock_parent_orm)，
        # 它的 `replies` 属性是一个包含 mock_reply_orm 的列表。
        mock_parent_orm = type(
            "MockComment",
            (),
            {
                "id": uuid4(),
                "content": "A top-level comment",
                "created_at": "2024-01-03T10:00:00",
                "author": type("MockUser", (), mock_author_data)(),
                "replies": [mock_reply_orm],
            },
        )()

        # 3. 使用 `CommentResponse.model_validate(mock_parent_orm)`
        # 来创建 Pydantic 对象。
        parent_response = CommentResponse.model_validate(mock_parent_orm)

        # 4. 断言：
        assert len(parent_response.replies) == 1
        assert isinstance(parent_response.replies[0], CommentResponse)
        assert parent_response.replies[0].content == "A reply comment"
