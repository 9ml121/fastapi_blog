"""
tests/test_schemas/test_post.py

测试 Post Pydantic Schemas
"""

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.post import PostCreate, PostResponse, PostUpdate
from app.schemas.user import UserResponse


class TestPostCreateSchema:
    """测试 PostCreate Schema"""

    def test_create_post_success(self):
        """测试：使用有效数据成功创建"""
        post = PostCreate(
            title="My First Post",
            content="This is the content of the post.",
            tags=["python", "fastapi"],
        )
        assert post.title == "My First Post"
        assert post.content == "This is the content of the post."
        assert post.tags == ["python", "fastapi"]
        # 在 schema 单元测试中，slug 未被提供，其值应为默认的 None
        # slug 的自动生成是 SQLAlchemy model 层的逻辑，不应在此测试
        assert post.slug is None

    def test_create_post_with_empty_title_raises_error(self):
        """测试：使用空标题创建会因 min_length=1 而失败"""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            PostCreate(title="", content="Some content")

    def test_create_post_missing_content_raises_error(self):
        """测试：缺少必填的 content 字段会失败"""
        with pytest.raises(ValidationError, match="Field required"):
            PostCreate(title="A valid title") # type: ignore


class TestPostUpdateSchema:
    """测试 PostUpdate Schema"""

    def test_update_post_with_all_fields_success(self):
        """测试：提供所有字段进行更新应该成功"""
        post_update = PostUpdate(
            title="Updated Title",
            content="Updated content.",
            summary="Updated summary.",
            tags=["updated"],
        )
        assert post_update.title == "Updated Title"
        assert post_update.tags == ["updated"]

    def test_update_post_with_empty_data_success(self):
        """测试：提供一个空字典进行更新也应该成功（因为所有字段都可选）"""
        try:
            post_update = PostUpdate()
            assert post_update.model_dump(exclude_unset=True) == {}
        except ValidationError:
            pytest.fail("PostUpdate with empty data should not raise ValidationError")

    def test_update_post_with_partial_data_success(self):
        """测试：只提供部分数据进行更新应该成功"""
        post_update = PostUpdate(
            title="Updated Title",
            summary="Updated summary.",
        )
        assert post_update.title == "Updated Title"
        assert post_update.summary == "Updated summary."
        assert post_update.content is None
        assert post_update.tags is None


class TestPostResponseSchema:
    """测试 PostResponse Schema"""

    def test_create_from_orm_model_success(self):
        """测试：能从一个模拟的 ORM 对象成功创建 Response Schema"""

        # 1. 创建一个模拟的 ORM User 对象 (或字典)
        mock_author = {
            "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "username": "testuser",
            "email": "test@example.com",
            "nickname": "Test User",
            "is_active": True,
            "role": "user",
            "avatar": None,
            "is_verified": True,
            "last_login": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }

        # 2. 创建一个模拟的 ORM Post 对象 (或字典)
        # 注意：它包含一个嵌套的 author 对象
        mock_post_orm = type('MockPost', (), {
            "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "title": "ORM Post Title",
            "content": "Content from ORM",
            "summary": "A summary",
            "slug": "orm-post-title", # 为 mock 对象提供 slug
            "tags": [], # 简单起见，tags 为空
            "author": type('MockUser', (), mock_author)(),
            "created_at": "2024-01-02T14:00:00",
            "updated_at": "2024-01-02T14:00:00",
            "published_at": None,
            "view_count": 100,
            "is_featured": False,
        })()

        # 3. 使用 from_attributes=True 的特性来创建 PostResponse 实例
        post_response = PostResponse.model_validate(mock_post_orm)

        # 4. 断言
        assert post_response.id == UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
        assert post_response.title == "ORM Post Title"
        assert isinstance(post_response.author, UserResponse) # 验证 author 字段被正确转换成了 UserResponse 类型
        assert post_response.author.username == "testuser"
        assert post_response.slug == "orm-post-title"
