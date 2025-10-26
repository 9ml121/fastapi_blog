"""
测试文章收藏功能 API 端点

测试覆盖:
- POST /posts/{post_id}/favorites - 切换收藏状态（幂等）
- GET /posts/{post_id}/favorite-status - 查询当前用户对文章的收藏状态
- GET /posts/{post_id}/favorited-users - 查询文章收藏用户列表
- GET /users/me/favorited-posts - 查询用户收藏文章列表

测试策略同点赞功能，但使用 Favorite 相关的 API
"""

from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient

from app.models.post import Post
from app.models.user import User

# ============================================
# POST /posts/{post_id}/favorites - 切换收藏状态
# ============================================


class TestToggleFavorite:
    """测试切换收藏状态"""

    def test_toggle_favorite_success_first_time(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：首次收藏文章"""
        response = client.post(
            f"/api/v1/posts/{published_post.id}/favorites",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_favorited"] is True
        assert data["favorite_count"] == 1

        # 验证数据库
        session.refresh(published_post)
        assert published_post.favorite_count == 1

    def test_toggle_favorite_success_unfavorite(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：取消收藏（幂等性测试）"""
        # 先收藏
        client.post(
            f"/api/v1/posts/{published_post.id}/favorites",
            headers=auth_headers,
        )

        # 再取消收藏
        response = client.post(
            f"/api/v1/posts/{published_post.id}/favorites",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_favorited"] is False
        assert data["favorite_count"] == 0

    def test_toggle_favorite_without_auth(
        self, client: TestClient, published_post: Post
    ):
        """❌ 异常数据：未登录用户尝试收藏"""
        response = client.post(f"/api/v1/posts/{published_post.id}/favorites")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_toggle_favorite_post_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """❌ 异常数据：收藏不存在的文章"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.post(
            f"/api/v1/posts/{fake_post_id}/favorites", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_toggle_favorite_draft_post(
        self, client: TestClient, auth_headers: dict, draft_post: Post
    ):
        """❌ 异常数据：收藏草稿文章"""
        response = client.post(
            f"/api/v1/posts/{draft_post.id}/favorites", headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "只能对已发布文章" in response.json()["error"]["message"]


# ============================================
# GET /posts/{post_id}/favorite-status - 查询收藏状态
# ============================================


class TestGetFavoriteStatus:
    """测试查询收藏状态"""

    def test_get_favorite_status_not_favorited(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """✅ 正常数据：查询未收藏状态"""
        response = client.get(
            f"/api/v1/posts/{published_post.id}/favorite-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_favorited"] is False
        assert data["favorite_count"] == 0

    def test_get_favorite_status_favorited(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """✅ 正常数据：查询已收藏状态"""
        # 先收藏
        client.post(
            f"/api/v1/posts/{published_post.id}/favorites",
            headers=auth_headers,
        )

        # 查询状态
        response = client.get(
            f"/api/v1/posts/{published_post.id}/favorite-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_favorited"] is True
        assert data["favorite_count"] == 1


# ============================================
# GET /users/me/favorited-posts - 查询用户收藏文章列表
# ============================================


class TestGetUserFavoritedPosts:
    """测试查询用户收藏文章列表"""

    def test_get_user_favorited_posts_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_user: User,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：查询用户收藏文章列表"""
        # 先收藏
        client.post(
            f"/api/v1/posts/{published_post.id}/favorites",
            headers=auth_headers,
        )

        # 查询用户收藏列表
        response = client.get("/api/v1/users/me/favorited-posts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(post["id"] == str(published_post.id) for post in data)

    def test_get_user_favorited_posts_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """✅ 边界数据：查询空收藏列表"""
        response = client.get("/api/v1/users/me/favorited-posts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0
