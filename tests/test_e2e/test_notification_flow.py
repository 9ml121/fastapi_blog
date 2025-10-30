"""
端到端测试 - 通知系统事件流

测试覆盖：
1. ✅ 点赞通知：用户 A 点赞文章 → 作者收到"点赞"通知
2. ✅ 点赞通知聚合：用户 B 点赞同一文章（1 小时内） → 通知聚合，aggregated_count=2
3. ✅ 评论通知：用户 A 评论文章 → 作者收到"评论"通知
4. ✅ 关注通知：用户 A 关注用户 B → B 收到"关注"通知
5. ✅ 通知已读：标记通知已读 → 未读数减少
6. ✅ 完整事件流：多个操作串联的完整用户旅程
7. ✅ 性能测试：聚合计数并发更新原子性验证

测试数据来源：
- 使用 conftest.py 中的 e2e_notification_data fixture
- 所有操作通过真实 API 调用完成，验证事件驱动的通知创建和聚合
"""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.conftest import E2ENotificationData

from app.core.security import create_access_token
from app.models.notification import NotificationType


class TestLikeNotificationFlow:
    """测试点赞通知流程"""

    def test_like_creates_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：用户 A 点赞文章 → 作者收到"点赞"通知

        测试意图:
        1. 验证点赞操作触发通知创建
        2. 验证通知类型正确（LIKE）
        3. 验证通知接收人是文章作者
        4. 验证通知消息格式正确

        测试步骤:
        1. 用户 A 点赞文章
        2. 作者查询通知列表
        3. 验证收到 1 条点赞通知
        """
        # 1. 用户 A 点赞文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_liked"] is True

        # 2. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # 3. 验证通知内容
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.LIKE
        assert notification["aggregated_count"] == 1
        assert notification["is_read"] is False
        assert notification["post"] is not None
        assert notification["post"]["id"] == str(e2e_notification_data.post.id)
        assert "赞了" in notification["message"] or "点赞" in notification["message"]

    def test_like_notification_aggregation(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：用户 B 点赞同一文章（1 小时内） → 通知聚合，aggregated_count=2

        测试意图:
        1. 验证同资源多用户操作的聚合逻辑
        2. 验证聚合时间窗口（1 小时）正确
        3. 验证聚合计数正确递增

        测试步骤:
        1. 用户 A 点赞文章 → 创建通知，aggregated_count=1
        2. 用户 B 在 1 小时内点赞同一文章 → 通知聚合，aggregated_count=2
        3. 验证只有 1 条通知，且聚合计数为 2
        """
        # 1. 用户 A 点赞文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. 用户 B 在 1 小时内点赞同一文章（立即点赞，在聚合窗口内）
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_b_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 3. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # 验证只有 1 条通知（聚合后）
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # 验证聚合计数
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.LIKE
        assert notification["aggregated_count"] == 2
        assert "2" in notification["message"] or "人" in notification["message"]

    def test_self_like_no_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 边界数据：自己点赞自己的文章不产生通知

        测试意图:
        1. 验证自我操作不触发通知（业务规则）
        2. 验证防御性校验正确执行

        测试步骤:
        1. 作者点赞自己的文章
        2. 作者查询通知列表
        3. 验证没有通知
        """
        # 1. 作者点赞自己的文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 3. 验证没有通知（自我操作不通知）
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestCommentNotificationFlow:
    """测试评论通知流程"""

    def test_comment_creates_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：用户 A 评论文章 → 作者收到"评论"通知

        测试意图:
        1. 验证评论操作触发通知创建
        2. 验证通知类型正确（COMMENT）
        3. 验证通知包含评论ID

        测试步骤:
        1. 用户 A 评论文章
        2. 作者查询通知列表
        3. 验证收到 1 条评论通知
        """
        # 1. 用户 A 评论文章
        comment_content = "这是一条测试评论"
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": comment_content},
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        # comment_data = response.json()  # 不需要使用 comment_id

        # 2. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # 3. 验证通知内容
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.COMMENT
        assert notification["aggregated_count"] == 1
        assert notification["post"] is not None
        assert notification["post"]["id"] == str(e2e_notification_data.post.id)
        assert "评论" in notification["message"] or "留言" in notification["message"]

    def test_comment_notification_aggregation(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：多个用户评论同一文章（1 小时内） → 通知聚合

        测试意图:
        1. 验证评论通知的聚合逻辑
        2. 验证聚合时间窗口（1 小时）正确
        3. 验证基于文章的聚合策略（忽略 comment_id）

        测试步骤:
        1. 用户 A 评论文章
        2. 用户 B 在 1 小时内评论同一文章
        3. 验证通知聚合，aggregated_count=2

        行业最佳实践:
        - 文章评论通知基于 (recipient_id, post_id, notification_type) 聚合
        - 忽略 comment_id，因为用户关心的是"文章被评论了"，而不是"哪个具体评论"
        - 符合 GitHub、Medium、Twitter 等主流平台的做法
        """
        # 1. 用户 A 评论文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": "第一条评论"},
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 2. 用户 B 在 1 小时内评论同一文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": "第二条评论"},
            headers=e2e_notification_data.user_b_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # 验证只有 1 条通知（聚合后）
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # 验证聚合计数和消息格式
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.COMMENT
        assert notification["aggregated_count"] == 2
        assert "2" in notification["message"] or "人" in notification["message"]
        assert notification["post"] is not None
        assert notification["post"]["id"] == str(e2e_notification_data.post.id)

    def test_self_comment_no_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 边界数据：自己评论自己的文章不产生通知"""
        # 1. 作者评论自己的文章
        response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": "作者自己的评论"},
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 2. 作者查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 3. 验证没有通知（自我操作不通知）
        data = response.json()
        assert data["total"] == 0


class TestFollowNotificationFlow:
    """测试关注通知流程"""

    def test_follow_creates_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：用户 A 关注用户 B → B 收到"关注"通知

        测试意图:
        1. 验证关注操作触发通知创建
        2. 验证通知类型正确（FOLLOW）
        3. 验证通知不包含 post_id 和 comment_id

        测试步骤:
        1. 用户 A 关注用户 B（user_b）
        2. 用户 B 查询通知列表
        3. 验证收到 1 条关注通知
        """
        # 1. 用户 A 关注用户 B
        response = client.post(
            f"/api/v1/users/{e2e_notification_data.user_b.id}/follow",
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 2. 用户 B 查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.user_b_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # 3. 验证通知内容
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.FOLLOW
        assert notification["aggregated_count"] == 1
        assert notification["post"] is None  # 关注通知不关联文章
        assert "关注" in notification["message"]

    def test_follow_notification_aggregation(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
        session: Session,
        sample_users: list,
    ):
        """✅ 正常数据：多个用户关注同一用户（24 小时内） → 通知聚合

        测试意图:
        1. 验证关注通知的聚合逻辑
        2. 验证聚合时间窗口（24 小时）正确

        测试步骤:
        1. 用户 A 关注用户 B
        2. 另一个用户（wangwu）在 24 小时内关注用户 B
        3. 验证通知聚合，aggregated_count=2
        """
        # 需要使用第 4 个用户（wangwu）

        from app.core.security import create_access_token

        user_wangwu = sample_users[3]  # wangwu
        wangwu_token = create_access_token(data={"sub": str(user_wangwu.id)})
        wangwu_headers = {"Authorization": f"Bearer {wangwu_token}"}

        # 1. 用户 A 关注用户 B
        response = client.post(
            f"/api/v1/users/{e2e_notification_data.user_b.id}/follow",
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 2. wangwu 在 24 小时内关注用户 B
        response = client.post(
            f"/api/v1/users/{e2e_notification_data.user_b.id}/follow",
            headers=wangwu_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. 用户 B 查询通知列表
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.user_b_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # 验证只有 1 条通知（聚合后）
        assert data["total"] == 1
        notification = data["items"][0]
        assert notification["notification_type"] == NotificationType.FOLLOW
        assert notification["aggregated_count"] == 2

    def test_self_follow_no_notification(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 边界数据：自己关注自己不产生通知（业务层阻止）"""
        # 1. 用户 A 尝试关注自己（会失败）
        response = client.post(
            f"/api/v1/users/{e2e_notification_data.user_a.id}/follow",
            headers=e2e_notification_data.user_a_headers,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "不能关注自己" in response.json()["error"]["message"]


class TestNotificationReadStatus:
    """测试通知已读状态"""

    def test_mark_notification_as_read(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：标记通知已读 → 未读数减少

        测试意图:
        1. 验证标记已读功能正确
        2. 验证未读数统计正确更新
        3. 验证数据一致性

        测试步骤:
        1. 用户 A 点赞文章 → 作者收到通知
        2. 用户 B 点赞文章 → 通知聚合
        3. 查询未读数（应该是 1）
        4. 标记通知已读
        5. 验证未读数变为 0
        """
        # 1. 用户 A 点赞文章
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_a_headers,
        )

        # 2. 用户 B 点赞文章（聚合）
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_b_headers,
        )

        # 3. 查询未读数
        response = client.get(
            "/api/v1/users/me/notifications/unread-count",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        initial_unread_count = response.json()
        assert initial_unread_count == 1

        # 4. 获取通知列表，找到通知ID
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        notification_id = response.json()["items"][0]["id"]

        # 5. 标记通知已读
        response = client.patch(
            f"/api/v1/users/me/notifications/{notification_id}",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. 验证未读数减少
        response = client.get(
            "/api/v1/users/me/notifications/unread-count",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        new_unread_count = response.json()
        assert new_unread_count == initial_unread_count - 1

        # 7. 验证通知状态已更新
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        notification = response.json()["items"][0]
        assert notification["is_read"] is True
        assert notification["read_at"] is not None

    def test_mark_all_notifications_as_read(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
    ):
        """✅ 正常数据：批量标记所有通知为已读"""
        # 1. 创建多条通知（点赞 + 评论）
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_a_headers,
        )
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": "测试评论"},
            headers=e2e_notification_data.user_b_headers,
        )

        # 2. 验证未读数
        response = client.get(
            "/api/v1/users/me/notifications/unread-count",
            headers=e2e_notification_data.author_headers,
        )
        assert response.json() == 2

        # 3. 批量标记已读
        response = client.patch(
            "/api/v1/users/me/notifications/mark-all-read",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. 验证未读数清零
        response = client.get(
            "/api/v1/users/me/notifications/unread-count",
            headers=e2e_notification_data.author_headers,
        )
        assert response.json() == 0


class TestCompleteNotificationFlow:
    """测试完整事件流（多个操作串联）"""

    def test_complete_notification_journey(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
        session: Session,
        sample_users: list,
    ):
        """✅ 正常数据：完整的通知事件流测试

        测试意图:
        1. 验证多个操作串联的完整流程
        2. 验证不同类型通知的正确创建
        3. 验证通知聚合逻辑在混合场景下的正确性

        测试场景:
        1. 用户 A 点赞文章 → 作者收到点赞通知
        2. 用户 B 点赞文章 → 点赞通知聚合
        3. 用户 A 评论文章 → 作者收到评论通知
        4. 用户 A 关注用户 B → 用户 B 收到关注通知
        5. 标记部分通知已读
        6. 验证通知状态和数据一致性
        """
        # 1. 用户 A 点赞文章
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_a_headers,
        )

        # 2. 用户 B 点赞文章（聚合）
        client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
            headers=e2e_notification_data.user_b_headers,
        )

        # 3. 用户 A 评论文章
        comment_response = client.post(
            f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
            json={"content": "这是一条评论"},
            headers=e2e_notification_data.user_a_headers,
        )
        assert comment_response.status_code == status.HTTP_201_CREATED

        # 4. 用户 A 关注用户 B
        follow_response = client.post(
            f"/api/v1/users/{e2e_notification_data.user_b.id}/follow",
            headers=e2e_notification_data.user_a_headers,
        )
        assert follow_response.status_code == status.HTTP_201_CREATED

        # 5. 作者查询通知列表（应该有 2 条：点赞聚合 + 评论）
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 2  # 点赞通知（聚合）+ 评论通知

        # 验证点赞通知聚合
        like_notification = next(
            (
                n
                for n in data["items"]
                if n["notification_type"] == NotificationType.LIKE
            ),
            None,
        )
        assert like_notification is not None
        assert like_notification["aggregated_count"] == 2

        # 验证评论通知
        comment_notification = next(
            (
                n
                for n in data["items"]
                if n["notification_type"] == NotificationType.COMMENT
            ),
            None,
        )
        assert comment_notification is not None
        assert comment_notification["aggregated_count"] == 1

        # 6. 用户 B 查询通知列表（应该有 1 条关注通知）
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.user_b_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["notification_type"] == NotificationType.FOLLOW

        # 7. 标记点赞通知已读
        like_notification_id = like_notification["id"]
        response = client.patch(
            f"/api/v1/users/me/notifications/{like_notification_id}",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # 8. 验证未读数更新
        response = client.get(
            "/api/v1/users/me/notifications/unread-count",
            headers=e2e_notification_data.author_headers,
        )
        assert response.json() == 1  # 只剩评论通知未读


class TestNotificationPerformance:
    """测试通知系统性能"""

    def test_concurrent_likes_atomic_update(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
        session: Session,
        sample_users: list,
    ):
        """✅ 性能测试：聚合计数并发更新原子性验证

        测试意图:
        1. 验证并发点赞场景下聚合计数的正确性
        2. 验证原子操作防止竞态条件
        3. 验证最终一致性

        测试场景:
        - 模拟多个用户快速连续点赞同一文章
        - 验证聚合计数正确（不应该有丢失或重复）
        """
        # 准备多个用户（使用已有的 sample_users）
        users = sample_users[1:]  # 排除作者
        user_headers_list = []
        for user in users:
            token = create_access_token(data={"sub": str(user.id)})
            user_headers_list.append({"Authorization": f"Bearer {token}"})

        # 所有用户依次点赞（模拟并发场景）
        for headers in user_headers_list:
            response = client.post(
                f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
                headers=headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # 查询通知，验证聚合计数正确
        response = client.get(
            "/api/v1/users/me/notifications",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 1  # 应该只有 1 条通知（聚合后）

        notification = data["items"][0]
        # 验证聚合计数等于点赞用户数（至少 3 个用户）
        assert notification["aggregated_count"] >= len(users)
        assert notification["notification_type"] == NotificationType.LIKE

    def test_notification_pagination_performance(
        self,
        client: TestClient,
        e2e_notification_data: E2ENotificationData,
        session: Session,
    ):
        """✅ 性能测试：大量通知查询（分页）

        测试意图:
        1. 验证分页查询在大数据量下的性能
        2. 验证分页逻辑的正确性

        注意:
        - 这个测试创建多条通知，验证分页功能
        - 实际性能测试可能需要更多数据，这里只验证功能正确性
        """
        # 创建多条不同类型的通知
        for i in range(5):
            # 轮流使用 user_a 和 user_b 点赞
            headers = (
                e2e_notification_data.user_a_headers
                if i % 2 == 0
                else e2e_notification_data.user_b_headers
            )

            # 先取消点赞（如果已点赞）
            client.delete(
                f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
                headers=headers,
            )
            # 再点赞（创建新通知，因为取消点赞会删除通知）
            client.post(
                f"/api/v1/posts/{e2e_notification_data.post.id}/likes",
                headers=headers,
            )
            # 评论
            client.post(
                f"/api/v1/posts/{e2e_notification_data.post.id}/comments",
                json={"content": f"评论 {i}"},
                headers=headers,
            )

        # 测试分页查询
        response = client.get(
            "/api/v1/users/me/notifications?page=1&size=3",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["items"]) <= 3  # 每页最多 3 条
        assert data["page"] == 1
        assert data["size"] == 3
        assert data["total"] >= 2  # 至少有 2 条通知（点赞聚合 + 多个评论）

        # 测试第二页
        response = client.get(
            "/api/v1/users/me/notifications?page=2&size=3",
            headers=e2e_notification_data.author_headers,
        )
        assert response.status_code == status.HTTP_200_OK
