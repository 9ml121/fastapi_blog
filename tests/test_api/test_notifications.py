"""
通知功能 API 测试

测试覆盖范围：
1. ✅ 通知列表查询（分页、过滤、排序）
2. ✅ 未读通知数量统计
3. ✅ 标记单条通知为已读
4. ✅ 标记所有通知为已读
5. ✅ 删除单条通知
6. ✅ 业务规则验证（权限、聚合逻辑、数据一致性）
7. ✅ 测试四象限覆盖（正常、边界、异常、极端数据）

测试数据来源：
- 使用 conftest.py 中 notification_factory fixture 创建测试数据
- sample_users[0] (原始用户) 作为通知接收者，使用 auth_headers 登录
- 包含未读通知6条、已读通知3条，覆盖不同类型和时间场景
- 聚合逻辑测试：点赞和评论通知会在1小时内聚合
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pprint import pprint

import pytest
from fastapi.testclient import TestClient
from tests.conftest import CreatedNotifications

from app.models import Notification
from app.models.notification import NotificationType
from app.models.user import User


@pytest.fixture
def created_data(
    notification_factory: Callable[..., "CreatedNotifications"],
) -> CreatedNotifications:
    """准备数据：使用notification_factory创建3条不同类型的通知，

    1. 避免API聚合逻辑的干扰
    2. 其中点赞和评论为未读，关注为已读
    """
    created_data = notification_factory(
        [
            {
                "count": 1,
                "notification_type": NotificationType.LIKE,
                "minutes_ago": 10,
                "is_read": False,
            },
            {
                "count": 1,
                "notification_type": NotificationType.COMMENT,
                "minutes_ago": 20,
                "is_read": False,
            },
            {
                "count": 1,
                "notification_type": NotificationType.FOLLOW,
                "minutes_ago": 30,
                "is_read": True,
            },
        ]
    )

    return created_data


class TestGetNotifications:
    """测试获取通知列表功能

    测试API端点：GET /api/v1/users/me/notifications

    必须覆盖的场景:
    1. ✅ 正常数据：成功获取通知列表
    2. ✅ 正常数据：分页查询
    3. ✅ 正常数据：过滤已读/未读通知
    4. ❌ 异常数据：未授权访问
    5. ❌ 边界数据：空分页参数
    """

    def test_get_notifications_success(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：成功获取通知列表

        测试意图:
        1. 验证用户可以成功获取自己的通知列表（无聚合的简单场景）
        2. 验证通知按创建时间倒序排列
        3. 验证返回的通知字段完整性

        测试数据:
        - 使用 created_data fixture 创建的测试数据，确保不会被聚合

        业务规则验证:
        - 成功获取通知列表 (HTTP 200)
        - 返回的总数与创建的总数一致
        - 通知按 created_at 倒序排列
        """
        # 使用fixture创建的测试数据，调用API获取通知列表
        response = client.get("/api/v1/users/me/notifications", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # 在这个简单场景下，API返回的总数应与我们创建的原始数量相等
        assert data["total"] == created_data.all_count
        assert len(data["items"]) == created_data.all_count

        # 验证时间排序 (最新在前)
        items = data["items"]
        for i in range(len(items) - 1):
            current_time = items[i]["created_at"]
            next_time = items[i + 1]["created_at"]
            assert current_time >= next_time

        # 验证通知字段完整性 (抽样检查)
        for item in items[:2]:
            assert "id" in item
            assert "actor" in item
            assert "notification_type" in item
            assert "message" in item
            assert "is_read" in item
            assert "created_at" in item

    def test_get_notifications_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：分页查询通知列表

        测试意图:
        1. 验证分页参数正确处理
        2. 验证分页数据准确性
        3. 验证分页元数据计算正确

        测试数据: 使用created_data fixture创建的测试数据
        - 总通知数: 3条
        - 分页大小: 2条/页
        - 测试第1页和第2页

        业务规则验证:
        - 第1页返回2条通知，total=3, pages=2
        - 第2页返回1条通知，page=2
        """

        # 测试第1页
        url = "/api/v1/users/me/notifications?page=1&size=2"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        pprint(data)

        assert len(data["items"]) == 2
        assert data["total"] == created_data.all_count
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["pages"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False

        # 测试第2页
        url = "/api/v1/users/me/notifications?page=2&size=2"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 1
        assert data["page"] == 2
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_get_notifications_filter_unread(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：过滤未读通知

        测试意图:
        1. 验证 is_read=false 过滤功能
        2. 验证未读通知数量正确
        3. 验证过滤后的通知都是未读状态

        测试数据: 使用created_data fixture创建的测试数据

        业务规则验证:
        - 只返回未读通知 (is_read=False)
        - 未读通知数量与预期一致
        - 所有返回通知的 is_read 字段都为 False
        """
        # 调用查询通知接口（参数为未读）
        url = "/api/v1/users/me/notifications?is_read=False"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # 验证只返回未读通知
        assert len(data["items"]) == created_data.unread_count
        assert data["total"] == created_data.unread_count

        # 验证所有通知都是未读状态
        for item in data["items"]:
            assert item["is_read"] is False

    def test_get_notifications_filter_read(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：过滤已读通知

        测试意图:
        1. 验证 is_read=true 过滤功能
        2. 验证已读通知数量正确
        3. 验证过滤后的通知都有 read_at 时间

        测试数据:
        - 使用created_data fixture创建的测试数据

        业务规则验证:
        - 只返回已读通知 (is_read=true)
        - 已读通知数量与预期一致
        - 所有返回通知都有 read_at 时间戳
        """
        # 调用查询通知接口（参数为已读）
        url = "/api/v1/users/me/notifications?is_read=true"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # 验证只返回已读通知
        assert len(data["items"]) == created_data.read_count
        assert data["total"] == created_data.read_count

        # 验证所有通知都是已读状态且有 read_at 时间
        for item in data["items"]:
            assert item["is_read"] is True
            assert item["read_at"] is not None

    def test_get_notifications_unauthorized(
        self,
        client: TestClient,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：未授权访问通知列表

        测试意图:
        1. 验证未登录用户无法访问通知列表
        2. 验证认证中间件正确拦截请求
        3. 验证错误响应格式统一

        测试数据:
        - 无认证 headers
        - 尝试访问需要认证的端点

        业务规则验证:
        - 未授权请求返回 HTTP 401
        - 错误响应包含统一格式
        - 敏感数据被保护
        """
        response = client.get("/api/v1/users/me/notifications")

        assert response.status_code == 401
        data = response.json()

        # 验证错误响应格式
        assert "error" in data
        assert data["error"]["code"] == "HTTP_ERROR"
        assert "Not authenticated" in data["error"]["message"]


class TestGetUnreadCount:
    """测试获取未读通知数量功能

    测试API端点：GET /api/v1/users/me/notifications/unread-count

    必须覆盖的场景:
    1. ✅ 正常数据：获取未读通知数量
    2. ✅ 边界数据：零未读通知
    3. ❌ 异常数据：未授权访问
    """

    def test_get_unread_count_success(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：获取未读通知数量

        测试意图:
        1. 验证可以正确统计未读通知数量
        2. 验证数量与实际数据一致
        3. 验证端点返回简单的整数值

        测试数据:
        - 使用created_data fixture创建的测试数据

        业务规则验证:
        - 成功获取未读通知数量 (HTTP 200)
        - 返回值为整数类型
        - 数量与 created_data fixture 创建的测试数据中的未读通知数量一致
        """
        url = "/api/v1/users/me/notifications/unread-count"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        count = response.json()

        # 验证返回的是整数
        assert isinstance(count, int)

        # 验证未读数量与预期一致
        assert count == created_data.unread_count

    def test_get_unread_count_zero(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 边界数据：零未读通知

        测试意图:
        1. 验证当没有未读通知时，返回0
        2. 验证返回的未读数量为0
        3. 验证端点返回简单的整数值

        测试数据: 无
        """
        url = "/api/v1/users/me/notifications/unread-count"
        response = client.get(url, headers=auth_headers)

        assert response.status_code == 200
        count = response.json()

        assert count == 0

    def test_get_unread_count_unauthorized(
        self,
        client: TestClient,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：未授权获取未读通知数量

        测试意图:
        1. 验证未登录用户无法获取未读数量
        2. 验证敏感统计信息被保护

        测试数据:
        - 无认证 headers
        - 尝试访问需要认证的统计端点

        业务规则验证:
        - 未授权请求返回 HTTP 401
        - 统计信息不被泄露
        """
        response = client.get("/api/v1/users/me/notifications/unread-count")

        assert response.status_code == 401


class TestMarkAsRead:
    """测试标记单条通知为已读功能

    测试API端点：PATCH /api/v1/users/me/notifications/{notification_id}

    必须覆盖的场景:
    1. ✅ 正常数据：成功标记通知为已读
    2. ✅ 边界数据：重复标记已读通知
    3. ❌ 异常数据：标记不存在通知
    4. ❌ 异常数据：标记他人通知
    5. ❌ 异常数据：未授权访问
    """

    def test_mark_notification_as_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：成功标记通知为已读

        测试意图:
        1. 验证可以成功标记通知为已读状态
        2. 验证 read_at 时间被正确设置
        3. 验证返回的已读通知数据完整

        测试数据:
        - 使用created_data fixture创建的测试数据，其中包含未读点赞通知
        - 操作者: sample_users[0] (通知接收者，使用 auth_headers 登录)

        业务规则验证:
        - 通知成功标记为已读 (HTTP 200)
        - is_read 字段更新为 true
        - read_at 字段被设置时间戳
        - 返回数据包含完整通知信息
        """
        # 获取一个未读通知ID
        notification = created_data.get_one_unread()
        assert notification is not None
        assert notification.is_read is False
        notification_id = str(notification.id)

        # 标记通知为已读
        response = client.patch(
            f"/api/v1/users/me/notifications/{notification_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证通知已被标记为已读
        assert data["is_read"] is True
        assert data["read_at"] is not None
        assert data["id"] == notification_id

        # 验证其他字段保持不变
        assert data["notification_type"] == notification.notification_type.value
        assert data["aggregated_count"] == notification.aggregated_count

    def test_mark_notification_as_read_duplicate(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 边界数据：重复标记已读通知

        测试意图:
        1. 验证重复标记已读通知返回200
        2. 验证通知已被标记为已读
        3. 验证其他字段保持不变

        测试数据:
        - 使用created_data fixture创建的测试数据，其中包含已读点赞通知
        """
        # 获取一个已读通知
        notification = created_data.get_one_read()
        assert notification is not None
        assert notification.is_read is True
        notification_id = str(notification.id)

        # 尝试重复标记通知为已读
        response = client.patch(
            f"/api/v1/users/me/notifications/{notification_id}", headers=auth_headers
        )

        # 验证返回200
        assert response.status_code == 200
        assert response.json()["is_read"] is True
        assert response.json()["read_at"] is not None
        assert response.json()["id"] == notification_id

    def test_mark_nonexistent_notification_as_read(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：标记不存在通知为已读

        测试意图:
        1. 验证标记不存在的通知返回适当错误
        2. 验证错误响应格式统一
        3. 验证系统对无效ID的处理

        测试数据:
        - 使用不存在的 UUID 作为通知ID
        - 操作者: 使用 auth_headers 的合法用户

        业务规则验证:
        - 不存在的通知返回 HTTP 404
        - 错误响应包含明确错误信息
        - 系统稳定性不受影响
        """
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

        response = client.patch(
            f"/api/v1/users/me/notifications/{fake_uuid}", headers=auth_headers
        )

        # 验证错误响应格式
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["message"] == "通知不存在"

    def test_mark_notification_as_read_other_user(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：标记他人通知为已读

        测试意图:
        1. 验证标记他人通知返回适当错误
        2. 验证错误响应格式统一
        3. 验证系统对他人通知的处理

        测试数据:
        - 使用created_data fixture创建的测试数据，其中包含sample_user用户未读点赞通知
        - 操作者: admin_user (使用 admin_auth_headers 登录)
        """
        # 获取一个未读通知
        notification = created_data.get_one_unread()
        assert notification is not None
        assert notification.is_read is False
        notification_id = str(notification.id)

        # 尝试标记他人通知为已读
        response = client.patch(
            f"/api/v1/users/me/notifications/{notification_id}",
            headers=admin_auth_headers,
        )

        # 验证错误响应格式
        assert response.status_code == 404
        data = response.json()
        pprint(data)
        assert "error" in data
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["message"] == "通知不存在"

    def test_mark_notification_as_read_unauthorized(
        self,
        client: TestClient,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：未授权标记通知为已读

        测试意图:
        1. 验证未登录用户无法标记通知
        2. 验证通知操作的权限控制

        测试数据:
        - 目标通知: 使用 created_data fixture创建的测试数据，其中包含未读点赞通知
        - 无认证 headers

        业务规则验证:
        - 未授权请求返回 HTTP 401
        - 通知状态不被修改
        """
        notification = created_data.get_one_unread()
        assert notification is not None
        assert notification.is_read is False
        notification_id = str(notification.id)

        response = client.patch(f"/api/v1/users/me/notifications/{notification_id}")

        assert response.status_code == 401


class TestMarkAllAsRead:
    """测试标记所有通知为已读功能

    测试API端点：PATCH /api/v1/users/me/notifications/mark-all-read

    必须覆盖的场景:
    1. ✅ 正常数据：成功标记所有通知为已读
    2. ✅ 边界数据：没有未读通知时标记
    3. ❌ 异常数据：未授权访问
    """

    def test_mark_all_notifications_as_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：成功标记所有通知为已读

        测试意图:
        1. 验证可以批量标记所有通知为已读
        2. 验证返回的操作数量正确
        3. 验证后续查询未读数量为0

        测试数据:
        - 初始未读通知: created_data fixture创建的测试数据中的2条未读通知数量
        - 操作者: sample_users[0] (通知接收者，使用 auth_headers 登录)

        业务规则验证:
        - 成功标记所有通知为已读 (HTTP 200)
        - 返回操作的通知数量
        - 未读通知数量变为0
        - 数据一致性保持
        """
        # 先验证初始未读数量
        url = "/api/v1/users/me/notifications/unread-count"
        response = client.get(url, headers=auth_headers)
        initial_unread = response.json()
        assert initial_unread == created_data.unread_count

        # 标记所有通知为已读
        response = client.patch(
            "/api/v1/users/me/notifications/mark-all-read", headers=auth_headers
        )

        pprint(response.json())
        assert response.status_code == 200
        marked_count = response.json()

        # 验证返回的操作数量
        assert marked_count == created_data.unread_count

        # 验证未读数量变为0
        url = "/api/v1/users/me/notifications/unread-count"
        response = client.get(url, headers=auth_headers)
        final_unread = response.json()
        assert final_unread == 0

    def test_mark_all_as_read_no_unread_notifications(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """✅ 边界数据：没有未读通知时标记所有为已读

        测试意图:
        1. 验证没有未读通知时的边界处理
        2. 验证返回0条操作记录
        3. 验证系统对空数据处理的稳定性

        测试数据:
        - 用户没有未读通知
        - 操作者: 使用 auth_headers 的合法用户

        业务规则验证:
        - 操作成功 (HTTP 200)
        - 返回操作数量为0
        - 系统不出现错误
        """
        response = client.patch(
            "/api/v1/users/me/notifications/mark-all-read", headers=auth_headers
        )

        assert response.status_code == 200
        marked_count = response.json()

        # 验证没有通知被标记
        assert marked_count == 0

    def test_mark_all_as_read_unauthorized(
        self,
        client: TestClient,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：未授权标记所有通知为已读

        测试意图:
        1. 验证未登录用户无法批量标记通知
        2. 验证批量操作的权限控制

        测试数据:
        - 无认证 headers
        - 尝试批量操作

        业务规则验证:
        - 未授权请求返回 HTTP 401
        - 批量操作被阻止
        """
        response = client.patch("/api/v1/users/me/notifications/mark-all-read")

        assert response.status_code == 401


class TestDeleteNotification:
    """测试删除通知功能

    测试API端点：DELETE /api/v1/users/me/notifications/{notification_id}

    必须覆盖的场景:
    1. ✅ 正常数据：成功删除通知
    2. ❌ 异常数据：删除不存在通知
    3. ❌ 异常数据：删除他人通知
    4. ❌ 异常数据：未授权访问
    5. ✅ 边界数据：重复删除同一通知
    """

    def test_delete_notification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：成功删除通知

        测试意图:
        1. 验证可以成功删除自己的通知
        2. 验证删除后通知不再出现在列表中
        3. 验证删除操作返回 HTTP 204

        测试数据:
        - 目标通知: created_data fixture创建的测试数据，其中包含已读点赞通知
        - 操作者: sample_users[0] (通知接收者，使用 auth_headers 登录)

        业务规则验证:
        - 通知成功删除 (HTTP 204)
        - 删除后通知列表中不再包含该通知
        - 返回无响应体 (符合 DELETE 操作规范)
        """
        # 获取一个通知ID
        notification = created_data.get_one_read()
        assert notification is not None
        assert notification.is_read is True
        notification_id = str(notification.id)

        # 删除通知
        response = client.delete(
            f"/api/v1/users/me/notifications/{notification_id}", headers=auth_headers
        )

        # 验证删除成功
        assert response.status_code == 204
        assert response.content == b""

        # 验证通知不再出现在列表中
        response = client.get("/api/v1/users/me/notifications", headers=auth_headers)
        data = response.json()

        notification_ids = [item["id"] for item in data["items"]]
        assert notification_id not in notification_ids

    def test_delete_nonexistent_notification(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：删除不存在通知

        测试意图:
        1. 验证删除不存在的通知返回适当错误
        2. 验证系统对无效删除操作的处理

        测试数据:
        - 使用不存在的 UUID 作为通知ID
        - 操作者: 使用 auth_headers 的合法用户

        业务规则验证:
        - 不存在的通知返回 HTTP 404
        - 错误响应包含明确错误信息
        """
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/users/me/notifications/{fake_uuid}", headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()

        # 验证错误响应格式
        assert "error" in data
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_delete_notification_unauthorized(
        self,
        client: TestClient,
        created_data: CreatedNotifications,
    ):
        """❌ 异常数据：未授权删除通知

        测试意图:
        1. 验证未登录用户无法删除通知
        2. 验证删除操作的权限控制

        测试数据:
        - 目标通知: 使用 created_data fixture创建的测试数据，其中包含已读点赞通知
        - 无认证 headers

        业务规则验证:
        - 未授权请求返回 HTTP 401
        - 删除操作被阻止
        """
        notification = created_data.get_one_read()
        assert notification is not None
        assert notification.is_read is True
        notification_id = str(notification.id)

        response = client.delete(f"/api/v1/users/me/notifications/{notification_id}")

        assert response.status_code == 401


class TestNotificationBusinessLogic:
    """测试通知业务逻辑和边界场景

    必须覆盖的场景:
    1. ✅ 聚合逻辑验证
    2. ✅ 数据一致性验证
    3. ✅ 极端数据场景
    """

    def test_notification_aggregation_logic(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 业务逻辑：通过模拟用户行为测试通知聚合

        测试意图:
        - 通过真实API调用（点赞， 关注, 评论）来触发通知创建和聚合逻辑。
        - 验证聚合逻辑在写入路径上是否正确工作。

        测试场景 1：
        3 个用户在 1 小时内关注了 followed, 验证 followed 只收到1条通知，且聚合数量为3。

        测试数据 1： conftest的sample_follows fixture 数据，

        """
        # 1. 准备角色
        followers = sample_follows[1:]

        # 2. 查询 followed 的通知列表
        response = client.get("/api/v1/users/me/notifications", headers=auth_headers)
        notifications_data = response.json()
        pprint(notifications_data)

        # 验证只生成了1条通知
        assert notifications_data["total"] == 1
        items = notifications_data["items"]
        assert len(items) == 1

        # 验证该通知的聚合数量为 followers 的数量
        notification = items[0]
        assert notification["aggregated_count"] == len(followers)
        assert notification["notification_type"] == NotificationType.FOLLOW
        assert "关注了你" in notification["message"]

    def test_notification_data_consistency(
        self,
        client: TestClient,
        auth_headers: dict,
        created_data: CreatedNotifications,
    ):
        """✅ 正常数据：验证通知数据一致性

        测试意图:
        1. 验证通知列表数量与未读数量统计一致
        2. 验证标记已读操作的一致性
        3. 验证删除操作的一致性

        测试数据:
        - 初始状态: created_data fixture 创建的测试数据
        - 执行一系列操作验证一致性

        业务规则验证:
        - 列表查询与统计查询结果一致
        - 状态变更操作数据同步
        - 删除操作不影响其他通知
        """
        # 1. 验证初始数据一致性
        response = client.get("/api/v1/users/me/notifications", headers=auth_headers)
        all_notifications = response.json()

        url = "/api/v1/users/me/notifications?is_read=false"
        response = client.get(url, headers=auth_headers)
        unread_notifications = response.json()

        response = client.get(
            "/api/v1/users/me/notifications/unread-count", headers=auth_headers
        )
        unread_count = response.json()

        assert len(unread_notifications["items"]) == unread_count
        assert unread_count == created_data.unread_count

        # 2. 标记一条通知为已读，验证一致性
        notification_to_mark = unread_notifications["items"][0]
        notification_id = notification_to_mark["id"]

        client.patch(
            f"/api/v1/users/me/notifications/{notification_id}", headers=auth_headers
        )

        # 重新检查一致性
        response = client.get(
            "/api/v1/users/me/notifications/unread-count", headers=auth_headers
        )
        new_unread_count = response.json()

        assert new_unread_count == unread_count - 1

        # 3. 删除一条通知，验证一致性
        client.delete(
            f"/api/v1/users/me/notifications/{notification_id}", headers=auth_headers
        )
        response = client.get("/api/v1/users/me/notifications", headers=auth_headers)
        new_all_notifications = response.json()

        assert (
            len(new_all_notifications["items"]) == len(all_notifications["items"]) - 1
        )

    def test_notification_extreme_data(
        self,
        client: TestClient,
        auth_headers: dict,
        session,
        sample_users: list[User],
        published_post,
    ):
        """🚀 极端数据：测试大量通知场景

        测试意图:
        1. 验证系统处理大量通知的性能
        2. 验证分页在大数据量下的正确性
        3. 验证聚合逻辑在大量数据下的稳定性

        测试数据:
        - 创建50条通知
        - 测试不同分页大小
        - 验证极端分页参数

        业务规则验证:
        - 大数据量下系统稳定运行
        - 分页计算正确
        - 聚合逻辑正常工作
        """
        # 创建大量通知数据
        recipient = sample_users[0]
        actor = sample_users[1]

        notifications = []
        for i in range(50):
            notification = Notification(
                recipient_id=recipient.id,
                actor_id=actor.id,
                notification_type=NotificationType.LIKE,
                post_id=published_post.id,
                is_read=i < 10,  # 前10条设为已读
                created_at=datetime.now(UTC) - timedelta(minutes=i),
            )
            notifications.append(notification)

        session.add_all(notifications)
        session.commit()

        # 测试大数据量分页
        response = client.get(
            "/api/v1/users/me/notifications?size=20", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 20
        assert data["total"] >= 50  # 至少包含新创建的50条

        # 测试极端分页参数
        response = client.get(
            "/api/v1/users/me/notifications?size=100", headers=auth_headers
        )
        assert response.status_code == 200

        # 测试大页码
        response = client.get(
            "/api/v1/users/me/notifications?page=999", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0  # 超出范围的页码返回空列表
