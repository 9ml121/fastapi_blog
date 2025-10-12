"""
测试文章管理 API 端点

测试覆盖:
- POST /posts - 创建文章
- GET /posts - 获取文章列表（分页）
- GET /posts/{post_id} - 获取单篇文章
- PATCH /posts/{post_id} - 更新文章（权限控制）
- DELETE /posts/{post_id} - 删除文章（权限控制）
"""

from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.post import post as post_crud
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate

# ============================================
# Fixtures - 测试数据和认证
# ============================================


@pytest.fixture
def post_data() -> dict:
    """API 测试用的文章数据"""
    return {
        "title": "测试文章标题",
        "content": "这是测试文章的内容，支持 **Markdown** 格式。",
        "summary": "文章摘要",
        "tags": ["Python", "FastAPI", "测试"],
    }


@pytest.fixture
def sample_post(session: Session, sample_user: User) -> Post:
    """创建一个示例文章用于测试"""
    post_in = PostCreate(
        title="示例文章",
        content="示例内容",
        summary="示例摘要",
        tags=["Tag1", "Tag2"],
    )
    return post_crud.create_with_author(
        db=session, obj_in=post_in, author_id=sample_user.id
    )


# ============================================
# 测试类：POST /posts - 创建文章
# ============================================


class TestCreatePost:
    """测试创建文章 API"""

    def test_create_post_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        post_data: dict,
        sample_user: User,
    ):
        """测试成功创建文章"""
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        # 1. 验证状态码
        assert response.status_code == status.HTTP_201_CREATED

        # 2. 验证响应数据结构
        data = response.json()
        assert data["title"] == post_data["title"]
        assert data["content"] == post_data["content"]
        assert data["summary"] == post_data["summary"]
        assert "id" in data
        assert "slug" in data  # 应该自动生成
        assert "created_at" in data

        # 3. 验证作者信息
        assert data["author"]["id"] == str(sample_user.id)
        assert data["author"]["username"] == sample_user.username

        # 4. 验证标签信息
        assert len(data["tags"]) == 3
        tag_names = {tag["name"] for tag in data["tags"]}
        # 注意：标签名称会被标准化（首字母大写）
        assert tag_names == {"Python", "Fastapi", "测试"}

        # 5. 验证数据库
        db_post = session.query(Post).filter(Post.id == UUID(data["id"])).first()
        assert db_post is not None
        assert db_post.title == post_data["title"]

    def test_create_post_without_auth(self, client: TestClient, post_data: dict):
        """测试未登录创建文章 - 应该返回 401"""
        response = client.post("/api/v1/posts/", json=post_data)
        # 注意：没有 headers 参数
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_post_with_custom_slug(
        self,
        client: TestClient,
        auth_headers: dict,
        post_data: dict,
    ):
        """测试使用自定义 slug 创建文章"""
        post_data["slug"] = "my-custom-slug-2025"

        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["slug"] == "my-custom-slug-2025"

    def test_create_post_duplicate_slug(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        post_data: dict,
        sample_user: User,
    ):
        """测试创建重复 slug 的文章 - 应该返回 409"""
        # 1. 先创建一篇文章
        post_in = PostCreate(title="第一篇", content="内容", slug="duplicate-slug")
        post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        # 2. 尝试创建相同 slug 的文章
        post_data["slug"] = "duplicate-slug"
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "slug" in response.json()["detail"].lower()

    # TODO(human): 添加更多创建文章的测试
    # 1. test_create_post_without_tags - 不提供 tags（应该成功，tags 为空）
    def test_create_post_without_tags(
        self,
        client: TestClient,
        auth_headers: dict,
        post_data: dict,
    ):
        """测试创建文章时没有提供 tags（应该成功，tags 为空）"""
        post_data.pop("tags")
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED

    # 2. test_create_post_invalid_data - 缺少必填字段（应该返回 422）
    def test_create_post_invalid_data(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """测试创建文章时缺少必填字段（应该返回 422）"""
        post_data = {"title": "缺少 content"}
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# 测试类：GET /posts - 获取文章列表
# ============================================


class TestGetPosts:
    """测试获取文章列表 API"""

    def test_get_posts_empty(self, client: TestClient):
        """测试获取空列表"""
        response = client.get("/api/v1/posts/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_posts_with_data(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
    ):
        """测试获取文章列表（有数据）"""
        # 创建 3 篇文章
        for i in range(3):
            post_in = PostCreate(title=f"文章 {i}", content=f"内容 {i}")
            post_crud.create_with_author(
                db=session, obj_in=post_in, author_id=sample_user.id
            )

        response = client.get("/api/v1/posts/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

        # 验证每篇文章的结构
        for post in data:
            assert "id" in post
            assert "title" in post
            assert "author" in post
            assert "tags" in post

    # TODO(human): 添加分页测试
    # 1. test_get_posts_pagination - 测试 skip 和 limit 参数
    def test_get_posts_pagination(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
    ):
        """测试 skip 和 limit 参数"""
        # 创建 10 篇文章
        for i in range(10):
            post_in = PostCreate(title=f"文章 {i}", content=f"内容 {i}")
            post_crud.create_with_author(
                db=session, obj_in=post_in, author_id=sample_user.id
            )

        #    - 测试 GET /posts?skip=0&limit=5 返回前 5 篇
        response = client.get("/api/v1/posts/?skip=0&limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        assert data[0]["title"] == "文章 0"
        assert data[-1]["title"] == "文章 4"

        #    - 测试 GET /posts?skip=5&limit=5 返回后 5 篇
        response = client.get("/api/v1/posts/?skip=5&limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        assert data[0]["title"] == "文章 5"
        assert data[-1]["title"] == "文章 9"


# ============================================
# 测试类：GET /posts/{post_id} - 获取单篇文章
# ============================================


class TestGetPost:
    """测试获取单篇文章详情 API"""

    def test_get_post_success(
        self,
        client: TestClient,
        sample_post: "Post",  # type: ignore
    ):
        """测试成功获取文章详情"""
        response = client.get(f"/api/v1/posts/{sample_post.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_post.id)
        assert data["title"] == sample_post.title
        assert data["content"] == sample_post.content

    # TODO(human): 添加获取文章的错误场景测试
    # 1. test_get_post_not_found - 不存在的 post_id（应该返回 404）
    #    - 使用一个随机的 UUID: "00000000-0000-0000-0000-000000000000"
    def test_get_post_not_found(
        self,
        client: TestClient,
    ):
        """测试获取不存在的文章（应该返回 404）"""
        response = client.get("/api/v1/posts/00000000-0000-0000-0000-000000000000")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # 2. test_get_post_invalid_uuid - 无效的 UUID 格式（应该返回 422）
    #    - 使用字符串 "invalid-uuid"
    def test_get_post_invalid_uuid(
        self,
        client: TestClient,
    ):
        """测试获取无效的 UUID（应该返回 422）"""
        response = client.get("/api/v1/posts/invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# 测试类：PATCH /posts/{post_id} - 更新文章
# ============================================
# 创建第二个用户的 fixture
@pytest.fixture
def other_user(session: Session) -> User:
    """创建第二个用户用于权限测试"""
    from app.crud.user import create_user
    from app.schemas.user import UserCreate

    user_in = UserCreate(
        username="other_user",
        email="other@example.com",
        password="Password123!",
    )
    return create_user(session, user_in=user_in)


@pytest.fixture
def other_user_headers(other_user: User) -> dict:
    """第二个用户的认证 headers"""
    token = create_access_token(data={"sub": str(other_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestUpdatePost:
    """测试更新文章 API"""

    def test_update_post_success(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
        auth_headers: dict,
    ):
        """测试作者成功更新自己的文章"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
        }

        response = client.patch(
            f"/api/v1/posts/{sample_post.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["summary"] == "更新后的摘要"
        # content 未更新，应该保持原值
        assert data["content"] == sample_post.content

    # TODO(human): 添加更新文章的权限和错误测试
    # 1. test_update_post_without_auth - 未登录（应该返回 401）
    def test_update_post_without_auth(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
    ):
        """测试未登录用户更新文章（应该返回 401）"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
        }

        response = client.patch(
            f"/api/v1/posts/{sample_post.id}",
            json=update_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. test_update_post_not_author - 非作者更新（应该返回 403）
    #    提示：需要创建第二个用户和他的 auth_headers
    def test_update_post_not_author(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
        other_user_headers: dict,
    ):
        """测试非作者更新文章（应该返回 403）"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
        }
        response = client.patch(
            f"/api/v1/posts/{sample_post.id}",
            json=update_data,
            headers=other_user_headers,  #  另一个用户的 token
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 3. test_update_post_not_found - 文章不存在（应该返回 404）
    def test_update_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """测试更新不存在的文章（应该返回 404）"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
        }
        response = client.patch(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # 4. test_update_post_tags - 更新标签（验证标签替换逻辑）
    def test_update_post_tags(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """测试更新文章的标签"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
            "tags": ["新标签1", "新标签2"],
        }

        response = client.patch(
            f"/api/v1/posts/{sample_post.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        tag_names = sorted({tag["name"] for tag in data["tags"]})
        assert len(tag_names) == 2
        assert tag_names == ["新标签1", "新标签2"]


# ============================================
# 测试类：DELETE /posts/{post_id} - 删除文章
# ============================================


class TestDeletePost:
    """测试删除文章 API"""

    def test_delete_post_success(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """测试作者成功删除自己的文章"""
        post_id = sample_post.id

        response = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers)

        # 1. 验证状态码（204 No Content）
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 2. 验证响应体为空
        assert response.text == ""

        # 3. 验证文章已被删除（再次获取应该 404）
        get_response = client.get(f"/api/v1/posts/{post_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    # TODO(human): 添加删除文章的权限和错误测试
    # 1. test_delete_post_without_auth - 未登录（应该返回 401）
    def test_delete_post_without_auth(
        self,
        client: TestClient,
        sample_post: Post,
    ):
        """测试未登录用户删除文章（应该返回 401）"""
        post_id = sample_post.id

        response = client.delete(f"/api/v1/posts/{post_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. test_delete_post_not_author - 非作者删除（应该返回 403）
    def test_delete_post_not_author(
        self,
        client: TestClient,
        sample_post: Post,
        other_user_headers: dict,
    ):
        """测试非作者删除文章（应该返回 403）"""
        post_id = sample_post.id

        response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=other_user_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # 3. test_delete_post_not_found - 文章不存在（应该返回 404）
    def test_delete_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """测试删除不存在的文章（应该返回 404）"""
        post_id = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
