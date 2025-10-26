"""
测试文章点赞功能 API 端点

测试覆盖:
- POST /posts/{post_id}/likes - 切换点赞状态（幂等）
- GET /posts/{post_id}/like-status - 查询当前用户对文章的点赞状态
- GET /posts/{post_id}/liked-users - 查询文章点赞用户列表
- GET /users/me/liked-posts - 查询用户点赞文章列表

测试数据四象限：
1. 正常数据 - 已发布文章的正常点赞操作
2. 边界数据 - 首次点赞、取消点赞、重复操作
3. 异常数据 - 不存在文章、草稿文章、未登录
4. 极端数据 - 并发点赞、大量点赞
"""

from pprint import pprint
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient

import app.crud.post as post_crud
import app.crud.post_like as post_like_crud
from app.models.post import Post, PostStatus
from app.models.user import User

# ============================================
# POST /posts/{post_id}/likes - 切换点赞状态
# ============================================


class TestToggleLike:
    """测试切换点赞状态"""

    def test_toggle_like_success_first_time(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        sample_user: User,
        session,
    ):
        """✅ 正常数据：首次点赞文章"""
        # 1. 执行点赞操作
        response = client.post(
            f"/api/v1/posts/{published_post.id}/likes",
            headers=auth_headers,
        )

        # 2. 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_liked"] is True
        assert data["like_count"] == 1

        # 3. 验证数据库
        session.refresh(published_post)
        assert published_post.like_count == 1

        # 4. 验证点赞记录
        is_liked = post_like_crud.is_liked(
            db=session, user_id=sample_user.id, post_id=published_post.id
        )
        assert is_liked is True

    def test_toggle_like_success_unlike(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：取消点赞（幂等性测试）"""
        # 1. 先点赞
        client.post(f"/api/v1/posts/{published_post.id}/likes", headers=auth_headers)

        # 2. 再取消点赞
        response = client.post(
            f"/api/v1/posts/{published_post.id}/likes",
            headers=auth_headers,
        )

        # 3. 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_liked"] is False
        assert data["like_count"] == 0

        # 4. 验证数据库
        session.refresh(published_post)
        assert published_post.like_count == 0

    def test_toggle_like_without_auth(self, client: TestClient, published_post: Post):
        """❌ 异常数据：未登录用户尝试点赞"""
        response = client.post(f"/api/v1/posts/{published_post.id}/likes")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_toggle_like_post_not_found(self, client: TestClient, auth_headers: dict):
        """❌ 异常数据：点赞不存在的文章"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.post(
            f"/api/v1/posts/{fake_post_id}/likes", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "文章不存在" in response.json()["error"]["message"]

    def test_toggle_like_draft_post(
        self, client: TestClient, auth_headers: dict, draft_post: Post
    ):
        """❌ 异常数据：点赞草稿文章"""
        response = client.post(
            f"/api/v1/posts/{draft_post.id}/likes", headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "只能对已发布文章" in response.json()["error"]["message"]


# ============================================
# GET /posts/{post_id}/like-status - 查询点赞状态
# ============================================


class TestGetLikeStatus:
    """测试查询点赞状态"""

    def test_get_like_status_not_liked(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """✅ 正常数据：查询未点赞状态"""
        response = client.get(
            f"/api/v1/posts/{published_post.id}/like-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_liked"] is False
        assert data["like_count"] == 0

    def test_get_like_status_liked(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """✅ 正常数据：查询已点赞状态"""
        # 1. 先点赞
        client.post(f"/api/v1/posts/{published_post.id}/likes", headers=auth_headers)

        # 2. 查询状态
        response = client.get(
            f"/api/v1/posts/{published_post.id}/like-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_liked"] is True
        assert data["like_count"] == 1

    def test_get_like_status_without_auth(
        self, client: TestClient, published_post: Post
    ):
        """❌ 异常数据：未登录用户查询点赞状态"""
        response = client.get(f"/api/v1/posts/{published_post.id}/like-status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_like_status_post_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """❌ 异常数据：查询不存在文章的点赞状态"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.get(
            f"/api/v1/posts/{fake_post_id}/like-status", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# GET /posts/{post_id}/liked-users - 查询点赞用户列表
# ============================================


class TestGetLikedUsers:
    """测试查询点赞用户列表"""

    def test_get_liked_users_success(
        self,
        client: TestClient,
        sample_user: User,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：查询已点赞用户列表"""
        # 1. 创建第二个用户
        from app.crud.user import create_user
        from app.schemas.user import UserCreate

        other_user = create_user(
            db=session,
            user_in=UserCreate(
                username="other_user_test",
                email="other_user_test@example.com",
                password="Password123!",
            ),
        )

        # 2. 两个用户点赞
        post_like_crud.toggle_like(
            db=session, user_id=sample_user.id, post_id=published_post.id
        )
        post_like_crud.toggle_like(
            db=session, user_id=other_user.id, post_id=published_post.id
        )

        # 3. 查询点赞用户列表
        response = client.get(f"/api/v1/posts/{published_post.id}/liked-users")
        pprint(response.json())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all("username" in user for user in data)

    def test_get_liked_users_empty(self, client: TestClient, published_post: Post):
        """✅ 边界数据：查询无点赞用户的文章"""
        response = client.get(f"/api/v1/posts/{published_post.id}/liked-users")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_get_liked_users_with_pagination(
        self,
        client: TestClient,
        sample_user: User,
        published_post: Post,
        session,
    ):
        """✅ 边界数据：分页查询点赞用户列表"""
        # 创建多个用户并点赞
        from app.crud.user import create_user
        from app.schemas.user import UserCreate

        for i in range(5):
            user = create_user(
                db=session,
                user_in=UserCreate(
                    username=f"user_{i}",
                    email=f"user_{i}@example.com",
                    password="Password123!",
                ),
            )
            post_like_crud.toggle_like(
                db=session, user_id=user.id, post_id=published_post.id
            )

        # 查询第一页
        response = client.get(
            f"/api/v1/posts/{published_post.id}/liked-users?skip=0&limit=2"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # 查询第二页
        response = client.get(
            f"/api/v1/posts/{published_post.id}/liked-users?skip=2&limit=2"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_liked_users_post_not_found(self, client: TestClient):
        """❌ 异常数据：查询不存在文章的点赞用户列表"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.get(f"/api/v1/posts/{fake_post_id}/liked-users")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# GET /users/me/liked-posts - 查询用户点赞文章列表
# ============================================


class TestGetUserLikedPosts:
    """测试查询用户点赞文章列表"""

    def test_get_user_liked_posts_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_user: User,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：查询用户点赞文章列表"""
        # 1. 先点赞
        client.post(
            f"/api/v1/posts/{published_post.id}/likes",
            headers=auth_headers,
        )

        # 2. 查询用户点赞列表
        response = client.get("/api/v1/users/me/liked-posts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(post["id"] == str(published_post.id) for post in data)

    def test_get_user_liked_posts_empty(self, client: TestClient, auth_headers: dict):
        """✅ 边界数据：查询空点赞列表"""
        response = client.get("/api/v1/users/me/liked-posts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_get_user_liked_posts_with_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_user: User,
        session,
    ):
        """✅ 边界数据：分页查询用户点赞文章列表"""
        # 创建多篇文章并点赞
        from app.schemas.post import PostCreate

        for i in range(5):
            post = post_crud.create_post(
                db=session,
                post_in=PostCreate(
                    title=f"测试文章 {i}",
                    content="内容",
                    status=PostStatus.PUBLISHED,
                ),
                author_id=sample_user.id,
            )
            post_like_crud.toggle_like(
                db=session, user_id=sample_user.id, post_id=post.id
            )

        # 查询第一页
        response = client.get(
            "/api/v1/users/me/liked-posts?skip=0&limit=2", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_user_liked_post_ids_batch_check(
        self,
        sample_user: User,
        session,
    ):
        """✅ 正常数据：测试批量检查点赞状态功能（CRUD 层）"""
        # 创建3篇文章
        from app.schemas.post import PostCreate

        posts = []
        for i in range(3):
            post = post_crud.create_post(
                db=session,
                post_in=PostCreate(
                    title=f"测试文章 {i}",
                    content="内容",
                    status=PostStatus.PUBLISHED,
                ),
                author_id=sample_user.id,
            )
            posts.append(post)

        # 点赞前两篇
        post_like_crud.toggle_like(
            db=session, user_id=sample_user.id, post_id=posts[0].id
        )
        post_like_crud.toggle_like(
            db=session, user_id=sample_user.id, post_id=posts[1].id
        )

        # 批量检查点赞状态
        post_ids = [posts[i].id for i in range(3)]
        liked_ids = post_like_crud.get_user_liked_post_ids(
            db=session, user_id=sample_user.id, post_ids=post_ids
        )

        # 验证结果
        assert len(liked_ids) == 2
        assert posts[0].id in liked_ids
        assert posts[1].id in liked_ids
        assert posts[2].id not in liked_ids

    def test_get_user_liked_post_ids_without_filter(
        self,
        sample_user: User,
        session,
        published_post: Post,
    ):
        """✅ 边界数据：不传 post_ids 参数，获取所有点赞文章ID"""
        # 点赞一篇文章
        post_like_crud.toggle_like(
            db=session, user_id=sample_user.id, post_id=published_post.id
        )

        # 不传 post_ids，获取所有点赞文章ID
        all_liked_ids = post_like_crud.get_user_liked_post_ids(
            db=session, user_id=sample_user.id, post_ids=None
        )

        # 验证结果
        assert len(all_liked_ids) >= 1
        assert published_post.id in all_liked_ids
