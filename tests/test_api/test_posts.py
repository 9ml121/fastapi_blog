"""
测试文章管理 API 端点

测试覆盖:
- POST /posts - 创建文章
- GET /posts - 获取文章列表（分页）
- GET /posts/drafts - 获取用户草稿列表 (Phase 6.1)
- GET /posts/{post_id} - 获取单篇文章
- PATCH /posts/{post_id} - 更新文章（权限控制）
- PATCH /posts/{post_id}/publish - 发布文章 (Phase 6.1)
- PATCH /posts/{post_id}/archive - 归档文章 (Phase 6.1)
- PATCH /posts/{post_id}/revert-to-draft - 回退为草稿 (Phase 6.1)
- DELETE /posts/{post_id} - 删除文章（权限控制）
"""

from pprint import pprint  # noqa: F401
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
# 共享 Fixtures
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


# ============================================
# POST /posts - 创建文章
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
        """✅ 正常数据：测试成功创建文章"""
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
        """✅ 异常数据：测试未登录创建文章 - 应该返回 401"""
        # 注意：没有 headers 参数
        response = client.post("/api/v1/posts/", json=post_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_post_with_custom_slug(
        self,
        client: TestClient,
        auth_headers: dict,
        post_data: dict,
    ):
        """✅ 正常数据：测试使用自定义 slug 创建文章"""
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
        """✅ 异常数据：测试创建重复 slug 的文章 - 应该返回 409"""
        # 1. 先创建一篇文章
        post_in = PostCreate(title="第一篇", content="内容", slug="duplicate-slug")
        post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        # 2. 尝试创建相同 slug 的文章
        post_data["slug"] = "duplicate-slug"
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        error_data = response.json()["error"]
        print(error_data)
        assert error_data["code"] == "DATABASE_INTEGRITY_ERROR"
        assert error_data["details"] is not None
        # 检查错误消息包含冲突相关信息
        assert "冲突" in error_data["message"] or "约束" in error_data["message"]

    def test_create_post_without_tags(
        self,
        client: TestClient,
        auth_headers: dict,
        post_data: dict,
    ):
        """✅ 边界数据：测试创建文章时没有提供 tags（应该成功，tags 为空）"""
        post_data.pop("tags")
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_post_invalid_data(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试创建文章时缺少必填字段（应该返回 422）"""
        post_data = {"title": "缺少 content"}
        response = client.post("/api/v1/posts/", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# GET /posts - 获取文章列表（分页）
# ============================================


class TestGetPosts:
    """测试获取文章列表 API"""

    def test_get_posts_empty(self, client: TestClient):
        """✅ 边界数据：测试获取空列表"""
        response = client.get("/api/v1/posts/")

        assert response.status_code == status.HTTP_200_OK
        print(response.json())
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0

    def test_get_posts_with_data(
        self,
        client: TestClient,
        sample_posts: list[Post],
    ):
        """✅ 正常数据：测试获取文章列表（有数据）"""
        response = client.get("/api/v1/posts/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["items"]
        assert len(data) == len(sample_posts)

        # 验证每篇文章的结构
        for post in data:
            assert "id" in post
            assert "title" in post
            assert "author" in post
            assert "tags" in post

    def test_get_posts_pagination(
        self,
        client: TestClient,
        sample_posts: list[Post],
    ):
        """✅ 正常数据：测试分页功能"""

        # 测试 GET /posts?page=1&size=5 返回前 5 篇
        response = client.get("/api/v1/posts/?page=1&size=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert data["total"] == len(sample_posts)
        assert data["pages"] == (len(sample_posts) + 5 - 1) // 5
        assert data["has_next"] is True
        assert data["has_prev"] is False
        # 测试默认按照 created_at 降序
        assert data["items"][0]["created_at"] >= data["items"][1]["created_at"]
        assert data["items"][1]["created_at"] >= data["items"][2]["created_at"]

    def test_get_posts_filter_by_title(
        self, client: TestClient, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能:按标题模糊查询过滤"""
        # 测试搜索 "示例" 关键词（适配简单 fixture）
        response = client.get("/api/v1/posts/?title_contains=python")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        print(data)

        # 验证所有返回的文章标题都包含"python"(忽略大小写)
        for post in data["items"]:
            assert "python" in post["title"].lower()

    def test_get_posts_filter_by_author(
        self, client: TestClient, sample_user: User, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能:按作者ID过滤"""
        response = client.get(f"/api/v1/posts/?author_id={sample_user.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证所有返回的文章都是该作者的
        for post in data["items"]:
            assert post["author"]["id"] == str(sample_user.id)

    def test_get_posts_filter_by_tag(
        self, client: TestClient, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能:按标签名称过滤"""
        response = client.get("/api/v1/posts/?tag_name=Tag1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证所有返回的文章都包含Tag1标签
        for post in data["items"]:
            tag_names = [tag["name"] for tag in post["tags"]]
            assert "Tag1" in tag_names

    def test_get_posts_filter_by_published_status(
        self, client: TestClient, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能:按发布状态过滤"""
        # 测试已发布文章 - 使用 statuses 参数
        response = client.get("/api/v1/posts/?statuses=published")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证所有返回的文章都是已发布状态（有 published_at 且不为 None）
        for post in data["items"]:
            # 只验证状态为 published 的文章
            if post["status"] == "published":
                assert post["published_at"] is not None

        # 测试未发布文章（草稿）- 使用 statuses 参数
        response = client.get("/api/v1/posts/?statuses=draft")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证所有返回的文章都是未发布状态（published_at 为 None 或 status 为 draft）
        for post in data["items"]:
            # 只验证状态为 draft 的文章
            if post["status"] == "draft":
                assert post["published_at"] is None

    def test_get_posts_filter_combined(
        self, client: TestClient, sample_user: User, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能:组合过滤条件"""
        response = client.get(
            f"/api/v1/posts/?author_id={sample_user.id}&tag_name=Tag1"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证所有文章都满足组合条件
        for post in data["items"]:
            assert post["author"]["id"] == str(sample_user.id)
            tag_names = [tag["name"] for tag in post["tags"]]
            assert "Tag1" in tag_names

    def test_get_posts_filter_edge_cases(
        self, client: TestClient, sample_posts: list[Post]
    ):
        """✅ 边界数据：测试过滤功能的边界情况"""
        # 测试不存在的作者ID
        response = client.get(
            "/api/v1/posts/?author_id=00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

        # 测试不存在的标签
        response = client.get("/api/v1/posts/?tag_name=NonExistentTag")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

        # 测试不存在的标题关键词
        response = client.get("/api/v1/posts/?title_contains=NonExistentTitle")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_posts_filter_with_pagination(
        self, client: TestClient, sample_user: User, sample_posts: list[Post]
    ):
        """✅ 正常数据：测试过滤功能与分页的组合"""
        response = client.get(
            f"/api/v1/posts/?author_id={sample_user.id}&page=1&size=3"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证分页信息
        assert data["page"] == 1
        assert data["size"] == 3
        assert len(data["items"]) <= 3

        # 验证所有文章都是该作者的
        for post in data["items"]:
            assert post["author"]["id"] == str(sample_user.id)


# ============================================
# GET /posts/drafts - 获取用户草稿列表 (Phase 6.1)
# ============================================


class TestGetUserDrafts:
    """测试获取用户草稿列表 API"""

    def test_get_user_drafts_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 正常数据：测试获取用户草稿列表"""
        # 创建一些草稿文章
        from app.schemas.post import PostCreate

        draft1 = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿1", content="内容1"),
            author_id=sample_user.id,
        )
        draft2 = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿2", content="内容2"),
            author_id=sample_user.id,
        )

        # 发布一篇文章（不应该出现在草稿列表中）
        published_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="已发布", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=published_post.id)

        response = client.get("/api/v1/posts/drafts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # 只有草稿

        # 验证只返回草稿
        draft_ids = {post["id"] for post in data}
        assert str(draft1.id) in draft_ids
        assert str(draft2.id) in draft_ids
        assert str(published_post.id) not in draft_ids

        # 验证按创建时间倒序排列
        assert data[0]["created_at"] >= data[1]["created_at"]

    def test_get_user_drafts_empty(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 边界数据：测试用户无草稿时返回空列表"""
        response = client.get("/api/v1/posts/drafts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_get_user_drafts_without_auth(self, client: TestClient):
        """✅ 异常数据：测试未登录获取草稿列表（应该返回 401）"""
        response = client.get("/api/v1/posts/drafts")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# GET /posts/{post_id} - 获取单篇文章
# ============================================


class TestGetPost:
    """测试获取单篇文章详情 API"""

    def test_get_post_success(
        self,
        client: TestClient,
        sample_post: "Post",  # type: ignore
    ):
        """✅ 正常数据：测试成功获取文章详情"""
        response = client.get(f"/api/v1/posts/{sample_post.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_post.id)
        assert data["title"] == sample_post.title
        assert data["content"] == sample_post.content

    def test_get_post_not_found(
        self,
        client: TestClient,
    ):
        """✅ 异常数据：测试获取不存在的文章（应该返回 404）"""
        response = client.get("/api/v1/posts/00000000-0000-0000-0000-000000000000")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_post_invalid_uuid(
        self,
        client: TestClient,
    ):
        """✅ 异常数据：测试获取无效的 UUID（应该返回 422）"""
        response = client.get("/api/v1/posts/invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# PATCH /posts/{post_id} - 更新文章
# ============================================


class TestUpdatePost:
    """测试更新文章 API"""

    def test_update_post_success(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
        auth_headers: dict,
    ):
        """✅ 正常数据：测试作者成功更新自己的文章"""
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

    def test_update_post_without_auth(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
    ):
        """✅ 异常数据：测试未登录用户更新文章（应该返回 401）"""
        update_data = {
            "title": "更新后的标题",
            "summary": "更新后的摘要",
        }

        response = client.patch(
            f"/api/v1/posts/{sample_post.id}",
            json=update_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_post_not_author(
        self,
        client: TestClient,
        sample_post: Post,  # type: ignore
        other_user_headers: dict,
    ):
        """✅ 异常数据：测试非作者更新文章（应该返回 403）"""
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

    def test_update_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试更新不存在的文章（应该返回 404）"""
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

    def test_update_post_tags(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 正常数据：测试更新文章的标签"""
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
# PATCH /posts/{post_id}/publish - 发布文章 (Phase 6.1)
# ============================================


class TestPublishPost:
    """测试发布文章 API"""

    def test_publish_post_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 正常数据：测试成功发布草稿"""
        # 创建草稿文章
        from app.schemas.post import PostCreate

        draft_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿文章", content="内容"),
            author_id=sample_user.id,
        )

        response = client.patch(
            f"/api/v1/posts/{draft_post.id}/publish", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None

    def test_publish_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试发布不存在的文章（应该返回 404）"""
        response = client.patch(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000/publish",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_publish_post_already_published(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试发布已发布的文章（应该返回 409）"""
        # 创建并发布文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)

        # 尝试再次发布
        response = client.patch(
            f"/api/v1/posts/{post.id}/publish", headers=auth_headers
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_publish_post_not_author(
        self,
        client: TestClient,
        session: Session,
        other_user_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试非作者发布文章（应该返回 403）"""
        # 创建草稿文章
        from app.schemas.post import PostCreate

        draft_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿", content="内容"),
            author_id=sample_user.id,
        )

        # 其他用户尝试发布
        response = client.patch(
            f"/api/v1/posts/{draft_post.id}/publish", headers=other_user_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_publish_post_without_auth(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
    ):
        """✅ 异常数据：测试未登录发布文章（应该返回 401）"""
        # 创建草稿文章
        from app.schemas.post import PostCreate

        draft_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿", content="内容"),
            author_id=sample_user.id,
        )

        response = client.patch(f"/api/v1/posts/{draft_post.id}/publish")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# PATCH /posts/{post_id}/archive - 归档文章 (Phase 6.1)
# ============================================


class TestArchivePost:
    """测试归档文章 API"""

    def test_archive_post_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 正常数据：测试成功归档已发布文章"""
        # 创建并发布文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)

        response = client.patch(
            f"/api/v1/posts/{post.id}/archive", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "archived"

    def test_archive_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试归档不存在的文章（应该返回 404）"""
        response = client.patch(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000/archive",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_archive_post_draft(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试归档草稿文章（应该返回 409）"""
        # 创建草稿文章
        from app.schemas.post import PostCreate

        draft_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿", content="内容"),
            author_id=sample_user.id,
        )

        response = client.patch(
            f"/api/v1/posts/{draft_post.id}/archive", headers=auth_headers
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_archive_post_not_author(
        self,
        client: TestClient,
        session: Session,
        other_user_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试非作者归档文章（应该返回 403）"""
        # 创建并发布文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)

        # 其他用户尝试归档
        response = client.patch(
            f"/api/v1/posts/{post.id}/archive", headers=other_user_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================
# PATCH /posts/{post_id}/revert-to-draft - 回退为草稿 (Phase 6.1)
# ============================================


class TestRevertToDraft:
    """测试回退为草稿 API"""

    def test_revert_published_to_draft_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 正常数据：测试成功将已发布文章回退为草稿"""
        # 创建并发布文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)

        response = client.patch(
            f"/api/v1/posts/{post.id}/revert-to-draft", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "draft"
        assert data["published_at"] is None

    def test_revert_archived_to_draft_success(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 正常数据：测试成功将已归档文章回退为草稿"""
        # 创建、发布并归档文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)
        post_crud.archive(db=session, post_id=post.id)

        response = client.patch(
            f"/api/v1/posts/{post.id}/revert-to-draft", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "draft"
        assert data["published_at"] is None

    def test_revert_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试回退不存在的文章（应该返回 404）"""
        response = client.patch(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000/revert-to-draft",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revert_already_draft(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试回退已是草稿的文章（应该返回 409）"""
        # 创建草稿文章
        from app.schemas.post import PostCreate

        draft_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="草稿", content="内容"),
            author_id=sample_user.id,
        )

        response = client.patch(
            f"/api/v1/posts/{draft_post.id}/revert-to-draft", headers=auth_headers
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_revert_post_not_author(
        self,
        client: TestClient,
        session: Session,
        other_user_headers: dict,
        sample_user: User,
    ):
        """✅ 异常数据：测试非作者回退文章（应该返回 403）"""
        # 创建并发布文章
        from app.schemas.post import PostCreate

        post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(title="文章", content="内容"),
            author_id=sample_user.id,
        )
        post_crud.publish(db=session, post_id=post.id)

        # 其他用户尝试回退
        response = client.patch(
            f"/api/v1/posts/{post.id}/revert-to-draft", headers=other_user_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================
# DELETE /posts/{post_id} - 删除文章
# ============================================


class TestDeletePost:
    """测试删除文章 API"""

    def test_delete_post_success(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 正常数据：测试作者成功删除自己的文章"""
        post_id = sample_post.id

        response = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers)

        # 1. 验证状态码（204 No Content）
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 2. 验证响应体为空
        assert response.text == ""

        # 3. 验证文章已被删除（再次获取应该 404）
        get_response = client.get(f"/api/v1/posts/{post_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_post_without_auth(
        self,
        client: TestClient,
        sample_post: Post,
    ):
        """✅ 异常数据：测试未登录用户删除文章（应该返回 401）"""
        post_id = sample_post.id

        response = client.delete(f"/api/v1/posts/{post_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_post_not_author(
        self,
        client: TestClient,
        sample_post: Post,
        other_user_headers: dict,
    ):
        """✅ 异常数据：测试非作者删除文章（应该返回 403）"""
        post_id = sample_post.id

        response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=other_user_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试删除不存在的文章（应该返回 404）"""
        post_id = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
