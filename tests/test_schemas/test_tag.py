"""
tests/test_schemas/test_tag.py

测试 Tag Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.tag import TagCreate, TagResponse, TagUpdate


class TestTagCreateSchema:
    """测试 TagCreate Schema"""

    def test_create_tag_success(self):
        """测试：使用有效数据成功创建"""
        tag = TagCreate(name="Python", description="All about Python")
        assert tag.name == "Python"
        assert tag.description == "All about Python"

    def test_create_tag_missing_name_fails(self):
        """测试：缺少必填的 name 字段会失败"""
        with pytest.raises(ValidationError):
            TagCreate(description="A description without a name") # type: ignore


class TestTagUpdateSchema:
    """测试 TagUpdate Schema"""

    def test_update_tag_with_partial_data_success(self):
        """测试：只提供部分数据进行更新应该成功"""
        tag = TagUpdate(description="A description without a name")
        assert tag.description == "A description without a name"
        assert tag.name is None


class TestTagResponseSchema:
    """测试 TagResponse Schema"""

    def test_create_from_orm_model_success(self):
        """测试：能从一个模拟的 ORM 对象成功创建 Response Schema"""
        mock_tag_orm = type('MockTag', (), {
            "id": uuid4(),
            "name": "FastAPI",
            "slug": "fastapi",
            "description": "A great web framework",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "post_count": 10, # 模拟有10篇文章
        })()

        tag_response = TagResponse.model_validate(mock_tag_orm)

        assert tag_response.name == "FastAPI"
        assert tag_response.slug == "fastapi"
        assert tag_response.post_count == 10
        assert isinstance(tag_response.id, UUID)
