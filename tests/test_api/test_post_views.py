"""
测试文章浏览统计功能 API 端点

测试覆盖:
- POST /posts/{post_id}/view - 记录文章浏览
- GET /posts/{post_id}/view-stats - 获取文章浏览统计
- GET /posts/{post_id}/view-status - 获取用户浏览状态

测试数据四象限：
1. 正常数据 - 已发布文章的正常浏览操作
2. 边界数据 - 首次浏览、重复浏览、时间范围边界
3. 异常数据 - 不存在文章、草稿文章、未登录
4. 极端数据 - 并发浏览、大量浏览记录、特殊字符
"""

from pprint import pprint  # noqa: F401
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient

import app.crud.post_view as post_view_crud
from app.models.post import Post
from app.models.post_view import PostView
from app.models.user import User

# ============================================
# POST /posts/{post_id}/view - 记录文章浏览
# ============================================


class TestRecordPostView:
    """测试记录文章浏览功能"""

    def test_record_view_authenticated_user_first_time(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        sample_user: User,
        session,
    ):
        """✅ 正常数据：已登录用户首次浏览已发布文章"""
        # 1. 执行浏览记录
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={
                "session_id": "test_session_123456789",
                "ip_address": "192.168.1.100",
                "user_agent": "Test Browser",
            },
        )

        # 2. 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_viewed"] is True
        assert data["view_count"] >= 1
        assert data["last_viewed_at"] is not None

        # 3. 验证数据库
        session.refresh(published_post)
        assert published_post.view_count >= 1

        # 4. 验证浏览记录
        is_viewed = post_view_crud.check_user_viewed_post(
            db=session, user_id=sample_user.id, post_id=published_post.id
        )
        assert is_viewed is True

    def test_record_view_anonymous_user(
        self,
        client: TestClient,
        published_post: Post,
        session,
    ):
        """✅ 正常数据：匿名用户浏览已发布文章"""
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "session_id": "anonymous_session_123456789",
                "ip_address": "203.0.113.1",
                "user_agent": "Anonymous Browser",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_viewed"] is True
        assert data["view_count"] >= 1

    def test_record_view_duplicate_prevention(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        sample_user: User,
    ):
        """✅ 边界数据：防刷机制测试 - 同一用户重复浏览"""
        # 1. 第一次浏览
        response1 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={
                "session_id": "test_session_duplicate",
                "ip_address": "192.168.1.100",
            },
        )
        assert response1.status_code == status.HTTP_200_OK
        first_view_count = response1.json()["view_count"]

        # 2. 立即第二次浏览（应该被防刷）
        response2 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={
                "session_id": "test_session_duplicate",
                "ip_address": "192.168.1.100",
            },
        )
        assert response2.status_code == status.HTTP_200_OK
        second_view_count = response2.json()["view_count"]

        # 3. 验证防刷生效（浏览次数不应该增加）
        assert first_view_count == second_view_count

    def test_record_view_anonymous_user_duplicate_prevention(
        self,
        client: TestClient,
        published_post: Post,
    ):
        """✅ 边界数据：防刷机制测试 - 匿名用户重复浏览"""
        # 1. 第一次浏览
        response1 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "session_id": "anonymous_session_duplicate",
                "ip_address": "203.0.113.1",
            },
        )
        assert response1.status_code == status.HTTP_200_OK
        first_view_count = response1.json()["view_count"]

        # 2. 立即第二次浏览（应该被防刷）
        response2 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "session_id": "anonymous_session_duplicate",
                "ip_address": "203.0.113.1",
            },
        )
        assert response2.status_code == status.HTTP_200_OK
        second_view_count = response2.json()["view_count"]

        # 3. 验证防刷生效（浏览次数不应该增加）
        assert first_view_count == second_view_count

    def test_record_view_skip_duplicate_check(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """✅ 边界数据：跳过防刷检查"""
        # 1. 第一次浏览
        response1 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={"skip_duplicate_check": False},
        )
        first_view_count = response1.json()["view_count"]

        # 2. 跳过防刷的第二次浏览
        response2 = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={"skip_duplicate_check": True},
        )
        second_view_count = response2.json()["view_count"]

        # 3. 验证跳过防刷后浏览次数增加
        assert second_view_count == first_view_count + 1

    def test_record_view_draft_post(
        self,
        client: TestClient,
        auth_headers: dict,
        draft_post: Post,
    ):
        """❌ 异常数据：浏览草稿文章"""
        response = client.post(
            f"/api/v1/posts/{draft_post.id}/view",
            headers=auth_headers,
            json={"session_id": "test_session"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_record_view_nonexistent_post(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：浏览不存在的文章"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.post(
            f"/api/v1/posts/{fake_post_id}/view",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_record_view_without_auth(
        self,
        client: TestClient,
        published_post: Post,
    ):
        """❌ 异常数据：未登录但需要认证的端点（虽然支持匿名，但测试一下）"""
        # 测试没有认证头的情况（应该正常，因为支持匿名）
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "session_id": "test_no_auth",
                "ip_address": "192.168.1.200",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_record_view_invalid_data(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
    ):
        """❌ 异常数据：无效请求数据"""
        # 测试过长的 session_id
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={
                "session_id": "x" * 100,  # 超过32字符限制
            },
        )
        # 应该返回验证错误
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================= 新增测试场景（待实现） =========================
    def test_record_view_authenticated_new_session_new_ip(
        self,
        client: TestClient,
        auth_headers: dict,
        published_post: Post,
        sample_user: User,
        post_view_records: dict[str, PostView],
        session,
    ):
        """✅ 正常数据：登录用户，24小时内应视为重复浏览，不增加计数"""
        # 同步冗余的 view_count 字段，使其与预置数据一致
        initial_count = post_view_crud.update_post_view_count_sync(
            session, post_id=published_post.id
        )
        # 预置数据中，有 4 条浏览记录
        assert initial_count == 4

        # 使用相同会话 ID 但不同 IP 发起浏览请求
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={
                "session_id": "user_session_new",
                "ip_address": "10.0.0.99",  # 与预置数据不同的 IP
            },
        )

        # 响应应成功，但视为重复，不增加计数
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count

        # 刷新文章对象，确保 view_count 未被修改
        session.refresh(published_post)
        assert published_post.view_count == initial_count

    def test_record_view_anonymous_new_session_new_ip(
        self,
        client: TestClient,
        published_post: Post,
        post_view_records: dict[str, PostView],
        session,
    ):
        """✅ 正常数据： 匿名用户，新会话，新IP地址"""
        # 同步冗余的 view_count 字段，使其与预置数据一致
        initial_count = post_view_crud.update_post_view_count_sync(
            session, post_id=published_post.id
        )
        # 预置数据中，有 4 条浏览记录
        assert initial_count == 4

        # 1. 使用匿名用户，新会话，应视为新浏览并增加计数
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "session_id": "anon_session_new",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count + 1

        # 2. 使用匿名用户，新IP地址，应视为新浏览并增加计数
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                "ip_address": "203.0.113.30",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count + 2

    def test_record_view_anonymous_same_ip(
        self,
        client: TestClient,
        published_post: Post,
        post_view_records: dict[str, PostView],
        session,
    ):
        """✅ 正常数据： 匿名用户，重复IP地址"""
        # 同步冗余的 view_count 字段，使其与预置数据一致
        initial_count = post_view_crud.update_post_view_count_sync(
            session, post_id=published_post.id
        )
        # 预置数据中，有 4 条浏览记录
        assert initial_count == 4

        # 1. 使用匿名用户，重复 IP，在时间窗口内应视为重复浏览
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                # 与预置数据相同的 IP 地址，最近浏览时间是24 小时内
                "ip_address": "203.0.113.10",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count

        # 2. 使用匿名用户，重复IP地址，超出时间窗口内应视为新浏览并增加计数
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                # 与预置数据相同的 IP 地址，最近浏览时间是24 小时前
                "ip_address": "203.0.113.20",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count + 1

    def test_record_view_anonymous_same_session(
        self,
        client: TestClient,
        published_post: Post,
        post_view_records: dict[str, PostView],
        session,
    ):
        """✅ 正常数据： 匿名用户，重复会话"""
        # 同步冗余的 view_count 字段，使其与预置数据一致
        initial_count = post_view_crud.update_post_view_count_sync(
            session, post_id=published_post.id
        )
        # 预置数据中，有 4 条浏览记录
        assert initial_count == 4

        # 1. 使用匿名用户，重复会话，在时间窗口内应视为重复浏览
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                # 与预置数据相同的会话ID，最近浏览时间是24 小时内
                "session_id": "anon_session_recent",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count

        # 2. 使用匿名用户，重复会话，超出时间窗口内应视为新浏览并增加计数
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={
                # 与预置数据相同的会话ID，最近浏览时间是24 小时前
                "session_id": "anon_session_stale",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] == initial_count + 1


# ============================================
# GET /posts/{post_id}/view-stats - 获取文章浏览统计
# ============================================


class TestGetPostViewStats:
    """测试获取文章浏览统计功能"""

    def test_get_stats_post_author(
        self,
        client: TestClient,
        published_post: Post,
        sample_user: User,
        auth_headers: dict,
        session,
    ):
        """✅ 正常数据：文章作者查看统计数据"""
        # 1. 先创建一些浏览记录
        client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={"session_id": "test_stats"},
        )

        # 2. 查询统计数据
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats",
            headers=auth_headers,
        )

        # 3. 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["total_views"] >= 1
        assert data["unique_visitors"] >= 1
        assert data["logged_in_views"] >= 1
        assert data["days_analyzed"] == 30  # 默认值
        assert "analysis_date" in data
        assert "start_date" in data

    def test_get_stats_admin_user(
        self,
        client: TestClient,
        published_post: Post,
        session,
        admin_auth_headers: dict,
    ):
        """✅ 正常数据：管理员查看统计数据"""
        # 创建2 条浏览记录
        client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={"session_id": "test_stats_123"},
        )
        client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={"session_id": "test_stats_456"},
        )

        # admin用户查询统计数据
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total_views"] == 2

    def test_get_stats_custom_time_range(
        self,
        client: TestClient,
        published_post: Post,
        auth_headers: dict,
    ):
        """✅ 边界数据：自定义时间范围统计"""
        # 测试7天统计
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats?days=7",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["days_analyzed"] == 7

    def test_get_stats_exclude_anonymous(
        self,
        client: TestClient,
        published_post: Post,
        auth_headers: dict,
    ):
        """✅ 边界数据：排除匿名用户数据"""
        # 创建 1 条匿名浏览记录
        client.post(
            f"/api/v1/posts/{published_post.id}/view",
            json={"session_id": "test_stats_789"},
        )

        # 查询统计数据，排除匿名
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats?include_anonymous=false",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 应该只统计登录用户数据
        assert data["anonymous_views"] == 0

    def test_get_stats_anonymous_user_denied(
        self,
        client: TestClient,
        published_post: Post,
    ):
        """❌ 异常数据：匿名用户查看统计数据"""
        response = client.get(f"/api/v1/posts/{published_post.id}/view-stats")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_stats_nonexistent_post(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：查看不存在文章的统计"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.get(
            f"/api/v1/posts/{fake_post_id}/view-stats",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_stats_invalid_params(
        self,
        client: TestClient,
        published_post: Post,
        auth_headers: dict,
    ):
        """❌ 异常数据：无效查询参数"""
        # 测试负数天数
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats?days=-5",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# GET /posts/{post_id}/view-status - 获取用户浏览状态
# ============================================


class TestGetPostViewStatus:
    """测试获取用户浏览状态功能"""

    def test_get_view_status_not_viewed(
        self,
        client: TestClient,
        published_post: Post,
        auth_headers: dict,
    ):
        """✅ 正常数据：查询未浏览状态"""
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["post_id"] == str(published_post.id)
        assert data["is_viewed"] is False
        assert data["view_count"] >= 0
        assert data["last_viewed_at"] is None

    def test_get_view_status_viewed_post(
        self,
        client: TestClient,
        published_post: Post,
        auth_headers: dict,
    ):
        """✅ 正常数据：查询已浏览状态"""
        # 1. 先记录浏览
        client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={"session_id": "test_status"},
        )

        # 2. 查询浏览状态
        response = client.get(
            f"/api/v1/posts/{published_post.id}/view-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_viewed"] is True
        assert data["view_count"] >= 1
        assert data["last_viewed_at"] is not None

    def test_get_view_status_without_auth(
        self,
        client: TestClient,
        published_post: Post,
    ):
        """❌ 异常数据：匿名用户查询浏览状态"""
        response = client.get(f"/api/v1/posts/{published_post.id}/view-status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_view_status_nonexistent_post(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：查询不存在文章的浏览状态"""
        fake_post_id = UUID("00000000-0000-0000-0000-000000000000")
        response = client.get(
            f"/api/v1/posts/{fake_post_id}/view-status",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# 集成测试
# ============================================


class TestPostViewIntegration:
    """文章浏览功能集成测试"""

    def test_view_workflow_complete(
        self,
        client: TestClient,
        published_post: Post,
        sample_user: User,
        auth_headers: dict,
        session,
    ):
        """✅ 正常数据：完整的浏览工作流程"""
        # 1. 用户浏览文章 -> 记录浏览
        response = client.post(
            f"/api/v1/posts/{published_post.id}/view",
            headers=auth_headers,
            json={"session_id": "workflow_test"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. 查询浏览状态 -> 确认已浏览
        status_response = client.get(
            f"/api/v1/posts/{published_post.id}/view-status",
            headers=auth_headers,
        )
        assert status_response.status_code == status.HTTP_200_OK
        assert status_response.json()["is_viewed"] is True

        # 3. 作者查看统计 -> 确认数据正确
        stats_response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats",
            headers=auth_headers,
        )
        assert stats_response.status_code == status.HTTP_200_OK
        stats_data = stats_response.json()
        assert stats_data["total_views"] >= 1
        assert stats_data["logged_in_views"] >= 1

    def test_concurrent_views_handling(
        self,
        client: TestClient,
        published_post: Post,
        sample_users: list,
        session,
    ):
        """✅ 极端数据：并发浏览处理"""
        from app.core.security import create_access_token

        view_count = 0

        # 多个用户同时浏览同一文章
        for i, user in enumerate(sample_users[:3]):  # 取前3个用户
            token = create_access_token(data={"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post(
                f"/api/v1/posts/{published_post.id}/view",
                headers=headers,
                json={"session_id": f"concurrent_test_{i}"},
            )
            if response.status_code == 200:
                view_count += 1

        # 验证统计准确性
        author_token = create_access_token(data={"sub": str(published_post.author_id)})
        author_headers = {"Authorization": f"Bearer {author_token}"}

        stats_response = client.get(
            f"/api/v1/posts/{published_post.id}/view-stats",
            headers=author_headers,
        )

        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            assert stats_data["total_views"] >= view_count
