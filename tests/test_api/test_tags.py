"""
测试标签管理 API 端点

测试覆盖:
- GET /tags - 获取标签列表（验证 post_count）
- GET /tags/{slug} - 获取标签详情（验证 posts 关联）
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.crud.post as post_crud
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate

# ============================================
# Fixtures - 测试数据
# ============================================


@pytest.fixture
def posts_with_tags(session: Session, sample_user: User) -> list[Post]:
    """创建多篇带标签的文章用于测试

    创建策略：
    - 文章 1：标签 ["Python", "FastAPI"]
    - 文章 2：标签 ["Python", "教程"]
    - 文章 3：标签 ["FastAPI"]

    结果：
    - "Python" 标签：post_count = 2
    - "Fastapi" 标签：post_count = 2
    - "教程" 标签：post_count = 1
    """
    posts = []

    # 文章 1
    post1 = post_crud.create_post(
        db=session,
        post_in=PostCreate(
            title="Python 基础教程",
            content="Python 入门内容",
            tags=["Python", "FastAPI"],
        ),
        author_id=sample_user.id,
    )
    posts.append(post1)

    # 文章 2
    post2 = post_crud.create_post(
        db=session,
        post_in=PostCreate(
            title="Python 进阶", content="Python 进阶内容", tags=["Python", "教程"]
        ),
        author_id=sample_user.id,
    )
    posts.append(post2)

    # 文章 3
    post3 = post_crud.create_post(
        db=session,
        post_in=PostCreate(
            title="FastAPI 实战", content="FastAPI 开发指南", tags=["FastAPI"]
        ),
        author_id=sample_user.id,
    )
    posts.append(post3)

    return posts


# ============================================
# 测试类：GET /tags - 获取标签列表
# ============================================


class TestGetTags:
    """测试获取标签列表 API"""

    def test_get_tags_empty(self, client: TestClient):
        """测试获取空标签列表"""
        response = client.get("/api/v1/tags/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_tags_with_data(
        self,
        client: TestClient,
        posts_with_tags: list[Post],  # 自动创建标签
    ):
        """测试获取标签列表（有数据）"""
        response = client.get("/api/v1/tags/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证标签数量（3 个唯一标签）
        assert len(data) == 3

        # 验证每个标签的结构
        for tag in data:
            assert "id" in tag
            assert "name" in tag
            assert "slug" in tag
            assert "post_count" in tag
            assert "created_at" in tag

    def test_get_tags_post_count_correct(
        self,
        client: TestClient,
        posts_with_tags: list[Post],
    ):
        """测试 post_count 统计正确"""
        response = client.get("/api/v1/tags/")
        data = response.json()

        # 将标签转换为字典，方便查找
        tags_dict = {tag["name"]: tag for tag in data}

        # 验证 "Python" 标签被 2 篇文章使用
        assert tags_dict["Python"]["post_count"] == 2

        # 验证 "Fastapi" 标签被 2 篇文章使用
        assert tags_dict["Fastapi"]["post_count"] == 2

        # 验证 "教程" 标签被 1 篇文章使用
        assert tags_dict["教程"]["post_count"] == 1

    #  添加分页测试
    def test_get_tags_pagination(self, client, session, sample_user):
        """测试标签列表分页功能"""
        # 提示：创建 10 个不同的标签（通过 10 篇文章）
        for i in range(10):
            post_crud.create_post(
                db=session,
                post_in=PostCreate(
                    title=f"文章 {i}",
                    content=f"内容 {i}",
                    tags=[f"Tag {i}"],  # ← 每篇文章用不同标签
                ),
                author_id=sample_user.id,
            )

        # 测试 skip=0&limit=5 和 skip=5&limit=5
        response1 = client.get("/api/v1/tags/?skip=0&limit=5")
        assert response1.status_code == status.HTTP_200_OK
        assert len(response1.json()) == 5
        assert response1.json()[0]["name"] == "Tag 0"
        assert response1.json()[-1]["name"] == "Tag 4"

        response2 = client.get("/api/v1/tags/?skip=5&limit=5")
        assert response2.status_code == status.HTTP_200_OK
        assert len(response2.json()) == 5
        assert response2.json()[0]["name"] == "Tag 5"
        assert response2.json()[-1]["name"] == "Tag 9"


# ============================================
# 测试类：GET /tags/{slug} - 获取标签详情
# ============================================


class TestGetTagBySlug:
    """测试获取标签详情 API"""

    def test_get_tag_by_slug_success(
        self,
        client: TestClient,
        posts_with_tags: list[Post],
    ):
        """测试成功获取标签详情"""
        # 获取 "python" 标签详情
        response = client.get("/api/v1/tags/python")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证标签基本信息
        assert data["name"] == "Python"
        assert data["slug"] == "python"
        assert data["post_count"] == 2

        # 验证 posts 字段存在且包含关联文章
        assert "posts" in data
        assert len(data["posts"]) == 2

        # 验证 posts 使用的是简化模型（PostInTag）
        for post in data["posts"]:
            assert "id" in post
            assert "title" in post
            assert "summary" in post
            assert "slug" in post
            assert "created_at" in post
            # 重要：验证不包含 tags 字段（避免循环引用）
            assert "tags" not in post

    def test_get_tag_by_slug_verify_posts_content(
        self,
        client: TestClient,
        posts_with_tags,
    ):
        """验证标签详情中的文章内容正确"""
        response = client.get("/api/v1/tags/python")
        data = response.json()

        # 获取文章标题列表
        post_titles = {post["title"] for post in data["posts"]}

        # 验证包含正确的文章
        assert "Python 基础教程" in post_titles
        assert "Python 进阶" in post_titles
        # 不应该包含只有 FastAPI 标签的文章
        assert "FastAPI 实战" not in post_titles

    #  添加标签不存在的测试
    def test_get_tag_by_slug_not_found(self, client):
        """测试获取不存在的标签 - 应该返回 404"""
        # 提示：使用不存在的 slug，如 "nonexistent-tag"
        response = client.get("/api/v1/tags/nonexistent-tag")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        print(response.json())
        assert response.json()["error"]["message"] == "标签不存在"

    #  添加中文 slug 测试
    def test_get_tag_by_slug_chinese(self, client, posts_with_tags):
        """测试使用中文 slug 获取标签"""
        # 提示：获取 "教程" 标签，验证返回正确
        response = client.get("/api/v1/tags/教程")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "教程"
        assert response.json()["slug"] == "教程"
        assert len(response.json()["posts"]) == 1
