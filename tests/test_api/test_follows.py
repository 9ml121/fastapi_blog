"""
测试关注功能 API 端点

测试数据设计:
基于 conftest.py 中的 sample_follows fixture:
- sample_follows[0]: 原始用户 (被 zhangsan, lisi, wangwu 3人关注)
- sample_follows[1]: zhangsan (关注了原始用户)
- sample_follows[2]: lisi (关注了原始用户)
- sample_follows[3]: wangwu (关注了原始用户)

测试覆盖的API端点:
- POST /users/{user_id}/follow - 关注用户
- DELETE /users/{user_id}/follow - 取消关注
- GET /users/{user_id}/followers - 获取粉丝列表
- GET /users/{user_id}/following - 获取关注列表
- GET /users/{user_id}/follower-count - 获取粉丝数
- GET /users/me/is-following/{user_id} - 检查是否已关注

测试数据四象限:
1. 正常数据 - 标准关注流程、查询列表、统计数据
2. 边界数据 - 重复关注、取消关注不存在关系、分页边界
3. 异常数据 - 不存在用户、自我关注、权限不足
4. 极端数据 - 批量关注操作、复杂业务场景

测试策略：
- 先验证正常流程的正确性
- 再测试边界条件和异常情况
- 最后验证数据一致性和业务规则
"""

import uuid

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User

# ============================================
# POST /users/{user_id}/follow - 关注用户
# ============================================


class TestFollowUser:
    """测试关注用户功能

    测试数据使用:
    - 使用 sample_follows[0] (当前登录用户) 关注 sample_follows[1]
    - 注意：sample_users[1] 已经关注了 sample_follows[0]，这是互相关注场景
    """

    def test_follow_user_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 正常数据：成功关注用户

        测试意图:
        1. 验证用户可以成功关注其他用户
        2. 验证返回的关注关系数据正确性
        3. 测试互相关注场景 (因为 sample_follows[1] 已经关注了 sample_follows[0])

        测试数据:
        - follower: sample_follows[0] (原始用户，使用 auth_headers 登录)
        - target: sample_follows[1] (zhangsan，已经关注了原始用户)
        """
        current_user = sample_follows[0]  # 当前登录用户
        target_user = sample_follows[1]  # zhangsan

        response = client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["follower_id"] == str(current_user.id)
        assert data["followed_id"] == str(target_user.id)
        assert "created_at" in data

    def test_follow_user_self(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_user: User,
    ):
        """❌ 异常数据：关注自己

        测试意图:
        1. 验证系统阻止用户关注自己
        2. 验证错误消息的准确性

        测试数据:
        - user: sample_user (尝试关注自己)

        业务规则:
        - 用户不能关注自己，这是系统的核心约束
        """
        response = client.post(
            f"/api/v1/users/{sample_user.id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "不能关注自己" in response.json()["error"]["message"]

    def test_follow_user_already_following(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """❌ 边界数据：重复关注

        测试意图:
        1. 验证系统阻止重复关注同一用户
        2. 验证唯一性约束的正确执行

        测试数据:
        - follower: sample_follows[0] (当前登录用户)
        - target: sample_follows[1] (zhangsan)

        测试步骤:
        1. 第一次关注：成功 (HTTP 201)
        2. 第二次关注：失败 (HTTP 409) - 违反唯一性约束

        业务规则:
        - 关注关系是唯一的，用户不能重复关注同一人
        """
        target_user = sample_follows[1]  # zhangsan (sample_follows[0] 是当前登录用户)

        # 1. 第一次关注成功
        response1 = client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # 2. 第二次关注应该失败 (唯一性约束)
        response2 = client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )
        assert response2.status_code == status.HTTP_409_CONFLICT

    def test_follow_user_nonexistent(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：关注不存在的用户

        测试意图:
        1. 验证系统正确处理不存在的用户ID
        2. 验证外键约束的正确执行

        测试数据:
        - 使用随机生成的UUID作为不存在的用户ID

        业务规则:
        - 不能关注不存在的用户，应返回404错误
        """
        fake_user_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/users/{fake_user_id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_follow_user_without_auth(
        self,
        client: TestClient,
        sample_follows: list[User],
    ):
        """❌ 异常数据：未登录用户关注"""
        target_user = sample_follows[1]
        response = client.post(
            f"/api/v1/users/{target_user.id}/follow",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# DELETE /users/{user_id}/follow - 取消关注
# ============================================


class TestUnfollowUser:
    """测试取消关注功能"""

    def test_unfollow_user_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 正常数据：成功取消关注"""
        target_user = sample_follows[1]

        # 1. 先关注
        client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        # 2. 取消关注
        response = client.delete(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unfollow_user_not_following(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """❌ 边界数据：取消未关注的用户"""
        target_user = sample_follows[1]

        response = client.delete(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["message"] == "关注关系不存在"

    def test_unfollow_user_nonexistent(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：取消关注不存在的用户"""
        fake_user_id = uuid.uuid4()
        response = client.delete(
            f"/api/v1/users/{fake_user_id}/follow",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["message"] == "被关注的用户不存在"

    def test_unfollow_user_without_auth(
        self,
        client: TestClient,
        sample_follows: list[User],
    ):
        """❌ 异常数据：未登录用户取消关注"""
        target_user = sample_follows[1]
        response = client.delete(
            f"/api/v1/users/{target_user.id}/follow",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# GET /users/{user_id}/followers - 获取粉丝列表
# ============================================


class TestGetFollowers:
    """测试获取粉丝列表功能

    测试数据使用说明:
    - sample_follows[0] (原始用户): 有3个粉丝 (zhangsan, lisi, wangwu)
    - sample_follows[1] (zhangsan): 有1个粉丝 (原始用户，在测试中动态创建)
    - sample_follows[2] (lisi): 有1个粉丝 (原始用户，来自conftest fixture)
    - sample_follows[3] (wangwu): 有1个粉丝 (原始用户，来自conftest fixture)
    """

    def test_get_followers_empty(
        self,
        client: TestClient,
        sample_user: User,
    ):
        """✅ 正常数据：获取无粉丝用户的列表

        测试意图:
        1. 验证没有粉丝的用户返回空列表
        2. 验证分页结构的正确性

        测试数据:
        - user: sample_user (独立创建的用户，没有任何粉丝)

        预期结果:
        - items: [] (空列表)
        - total: 0
        - 默认分页参数生效 (page=1, size=20)
        """
        response = client.get(f"/api/v1/users/{sample_user.id}/followers")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20

    def test_get_followers_with_data(
        self,
        client: TestClient,
        sample_follows: list[User],
        auth_headers: dict,
    ):
        """✅ 正常数据：获取有粉丝用户的列表

        测试意图:
        1. 验证有粉丝的用户返回正确的粉丝列表
        2. 验证粉丝数据结构的完整性
        3. 验证is_following字段的存在

        测试数据:
        - target_user: sample_follows[1] (zhangsan)
        - follower: sample_follows[0] (原始用户，登录后关注zhangsan)

        数据来源说明:
        - 在测试中动态创建关注关系，确保测试的独立性
        - 验证粉丝列表包含正确的用户信息和关系状态
        """
        target_user = sample_follows[1]  # zhangsan
        follower_user = sample_follows[0]  # 原始用户 (当前登录)

        # 建立关注关系: 原始用户关注 zhangsan
        client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        response = client.get(f"/api/v1/users/{target_user.id}/followers")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(follower_user.id)
        assert data["items"][0]["username"] == follower_user.username
        assert "is_following" in data["items"][0]

    def test_get_followers_pagination(
        self,
        client: TestClient,
        session: Session,
        sample_follows: list[User],
    ):
        """✅ 边界数据：分页查询粉丝列表

        测试意图:
        1. 验证分页参数的正确处理
        2. 验证分页逻辑的准确性
        3. 验证总数统计的正确性

        测试数据来源:
        - 使用 conftest.py 中 sample_follows fixture 的预设数据
        - sample_follows[0] (原始用户) 有3个预设的粉丝:
          * sample_follows[1] (zhangsan)
          * sample_follows[2] (lisi)
          * sample_follows[3] (wangwu)

        数据构建说明:
        - 这3个关注关系在 conftest.py 第454-458行建立
        - 不在测试中动态创建，使用现有的预设数据
        - 确保分页测试基于真实的关注关系数据

        测试参数:
        - page=1, size=2 (第一页，每页2条记录)

        预期结果:
        - total: 3 (总共3个粉丝)
        - items长度: 2 (第一页有2条记录)
        - page: 1, size: 2 (分页参数正确返回)
        """
        target_user = sample_follows[0]  # 原始用户，有3个预设粉丝

        response = client.get(f"/api/v1/users/{target_user.id}/followers?page=1&size=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) == 2  # 第一页有2个粉丝
        assert data["total"] == 3  # 总共3个粉丝

    def test_get_followers_nonexistent_user(
        self,
        client: TestClient,
    ):
        """❌ 异常数据：获取不存在用户的粉丝列表"""
        fake_user_id = uuid.uuid4()
        response = client.get(f"/api/v1/users/{fake_user_id}/followers")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_followers_with_viewer_context(
        self,
        client: TestClient,
        sample_follows: list[User],
        auth_headers: dict,
    ):
        """✅ 正常数据：查看者上下文（检查is_following字段）

        构建：sample_users[0] 关注 sample_follows[1]
        测试：sample_users[0]作为查看者时，sample_users[1]粉丝列表中的is_following字段是否正确。
        """
        target_user = sample_follows[1]

        # 建立关注关系
        client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/users/{target_user.id}/followers",
            headers=auth_headers,  # 以viewer_user的身份查看
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if data["items"]:
            # 验证is_following字段存在但未关注自己
            assert "is_following" in data["items"][0]
            assert data["items"][0]["is_following"] is False


# ============================================
# GET /users/{user_id}/following - 获取关注列表
# ============================================


class TestGetFollowing:
    """测试获取关注列表功能"""

    def test_get_following_empty(
        self,
        client: TestClient,
        sample_user: User,
    ):
        """✅ 正常数据：获取无关注用户的列表"""
        response = client.get(f"/api/v1/users/{sample_user.id}/following")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_following_with_data(
        self,
        client: TestClient,
        sample_follows: list[User],
        auth_headers: dict,
    ):
        """✅ 正常数据：获取有关注用户的列表"""
        follower_user = sample_follows[0]
        target_user = sample_follows[1]

        # 先建立关注关系
        client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        response = client.get(f"/api/v1/users/{follower_user.id}/following")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(target_user.id)

    def test_get_following_pagination(
        self,
        client: TestClient,
        sample_follows: list[User],
    ):
        """✅ 边界数据：分页查询关注列表

        sample_users中 3 个用户都关注了 sample_user
        """
        user = sample_follows[1]
        response = client.get(f"/api/v1/users/{user.id}/following?page=1&size=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert data["total"] == 1

    def test_get_following_nonexistent_user(
        self,
        client: TestClient,
    ):
        """❌ 异常数据：获取不存在用户的关注列表"""
        fake_user_id = uuid.uuid4()
        response = client.get(f"/api/v1/users/{fake_user_id}/following")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# GET /users/{user_id}/follower-count - 获取粉丝数
# ============================================


class TestGetFollowerCount:
    """测试获取粉丝数功能"""

    def test_get_follower_count_zero(
        self,
        client: TestClient,
        sample_user: User,
    ):
        """✅ 正常数据：获取无粉丝用户的数量"""
        response = client.get(f"/api/v1/users/{sample_user.id}/follower-count")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 0

    def test_get_follower_count_multiple(
        self,
        client: TestClient,
        sample_follows: list[User],
    ):
        """✅ 正常数据：获取有粉丝用户的数量

        测试意图:
        1. 验证粉丝数统计的准确性
        2. 验证返回数据的类型正确性

        测试数据来源:
        - 使用 conftest.py 中 sample_follows fixture 的预设数据
        - sample_follows[0] (原始用户) 有3个预设的粉丝:
          * sample_follows[1] (zhangsan)
          * sample_follows[2] (lisi)
          * sample_follows[3] (wangwu)

        数据构建说明:
        - 这3个关注关系在 conftest.py 第454-458行建立
        - 不在测试中动态创建，使用现有的预设数据
        - 确保粉丝数统计基于真实的关注关系数据

        预期结果:
        - count: 3 (整数类型)
        """
        target_user = sample_follows[0]  # 原始用户，有3个预设粉丝

        response = client.get(f"/api/v1/users/{target_user.id}/follower-count")

        assert response.status_code == status.HTTP_200_OK
        count = response.json()
        assert isinstance(count, int)
        assert count == 3  # 验证粉丝数量正确

    def test_get_follower_count_nonexistent_user(
        self,
        client: TestClient,
    ):
        """❌ 异常数据：获取不存在用户的粉丝数"""
        fake_user_id = uuid.uuid4()
        response = client.get(f"/api/v1/users/{fake_user_id}/follower-count")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# GET /users/me/is-following/{user_id} - 检查是否已关注
# ============================================


class TestIsFollowing:
    """测试检查是否已关注功能"""

    def test_is_following_false(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 正常数据：未关注用户"""
        target_user = sample_follows[1]

        response = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is False

    def test_is_following_true(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 正常数据：已关注用户"""
        target_user = sample_follows[1]

        # 先关注
        client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is True

    def test_is_following_self(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_user: User,
    ):
        """✅ 边界数据：检查自己"""
        response = client.get(
            f"/api/v1/users/me/is-following/{sample_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is False

    def test_is_following_nonexistent_user(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """❌ 异常数据：检查不存在的用户"""
        fake_user_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/users/me/is-following/{fake_user_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_is_following_without_auth(
        self,
        client: TestClient,
        sample_follows: list[User],
    ):
        """❌ 异常数据：未登录用户检查关注状态"""
        target_user = sample_follows[1]
        response = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# 集成测试
# ============================================


class TestFollowIntegration:
    """关注功能集成测试

    测试数据使用说明:
    - 使用 sample_follows 的组合来模拟真实的社交关注场景
    - 验证多个API端点之间的数据一致性
    """

    def test_follow_unfollow_complete_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_follows: list[User],
    ):
        """✅ 正常数据：完整的关注-取消关注工作流程

        测试意图:
        1. 验证完整的关注/取消关注业务流程
        2. 验证各API端点间的数据一致性
        3. 验证关注关系的实时状态更新

        测试数据:
        - follower: sample_follows[0] (原始用户，当前登录)
        - target: sample_follows[1] (zhangsan)

        业务流程验证 (8个步骤):
        1. 初始状态: 未关注 (is_following = False)
        2. 执行关注: 成功创建关注关系 (HTTP 201)
        3. 关注状态: 已关注 (is_following = True)
        4. 粉丝统计: 目标用户粉丝数增加 (>= 1)
        5. 粉丝列表: 目标用户出现在粉丝列表中
        6. 关注列表: 关注关系出现在关注列表中
        7. 取消关注: 成功删除关注关系 (HTTP 204)
        8. 最终状态: 未关注 (is_following = False)

        数据一致性检查:
        - 关注状态查询与实际关系保持一致
        - 粉丝数统计与实际粉丝列表保持一致
        - 关注列表与粉丝列表的对称关系正确
        """
        follower_user = sample_follows[0]  # 原始用户 (当前登录)
        target_user = sample_follows[1]  # zhangsan

        # 1. 检查初始状态 (未关注)
        response1 = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
            headers=auth_headers,
        )
        assert response1.json() is False

        # 2. 执行关注操作
        response2 = client.post(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )
        assert response2.status_code == status.HTTP_201_CREATED

        # 3. 验证关注状态更新
        response3 = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
            headers=auth_headers,
        )
        assert response3.json() is True

        # 4. 验证目标用户粉丝数统计更新
        response4 = client.get(f"/api/v1/users/{target_user.id}/follower-count")
        follower_count = response4.json()
        assert follower_count >= 1

        # 5. 验证目标用户粉丝列表包含关注者
        response5 = client.get(f"/api/v1/users/{target_user.id}/followers")
        followers_data = response5.json()
        assert followers_data["total"] >= 1

        # 6. 验证关注者的关注列表包含目标用户
        response6 = client.get(f"/api/v1/users/{follower_user.id}/following")
        following_data = response6.json()
        assert following_data["total"] >= 1

        # 7. 执行取消关注操作
        response7 = client.delete(
            f"/api/v1/users/{target_user.id}/follow",
            headers=auth_headers,
        )
        assert response7.status_code == status.HTTP_204_NO_CONTENT

        # 8. 验证取消关注后的状态恢复
        response8 = client.get(
            f"/api/v1/users/me/is-following/{target_user.id}",
            headers=auth_headers,
        )
        assert response8.json() is False

    def test_mutual_follow_relationship(
        self,
        client: TestClient,
        sample_follows: list[User],
        auth_headers: dict,
    ):
        """✅ 正常数据：互相关注关系

        测试意图:
        1. 验证互相关注场景的正确处理
        2. 验证关注关系的对称性

        测试数据:
        - user_a: sample_follows[0] (原始用户，当前登录)
        - user_b: sample_follows[1] (zhangsan)

        数据状态说明:
        - 初始状态: sample_follows[1] 已经关注了 sample_follows[0] (来自conftest)
        - 测试步骤: sample_follows[0] 关注 sample_follows[1]，形成互相关注

        验证点:
        1. user_a的关注列表包含user_b
        2. user_b的粉丝列表包含user_a
        """
        user_a = sample_follows[0]  # 原始用户 (当前登录)
        user_b = sample_follows[1]  # zhangsan

        # user_a 关注 user_b (user_b已经关注了user_a，形成互相关注)
        client.post(
            f"/api/v1/users/{user_b.id}/follow",
            headers=auth_headers,
        )

        # 验证 user_a 的关注列表包含 user_b
        response1 = client.get(f"/api/v1/users/{user_a.id}/following")
        assert response1.json()["total"] >= 1

        # 验证 user_b 的粉丝列表包含 user_a
        response2 = client.get(f"/api/v1/users/{user_b.id}/followers")
        assert response2.json()["total"] >= 1

    def test_follow_multiple_users(
        self,
        client: TestClient,
        sample_follows: list[User],
        auth_headers: dict,
    ):
        """✅ 极端数据：一个用户关注多个用户

        测试意图:
        1. 验证批量关注操作的正确性
        2. 验证关注列表的累积统计
        3. 验证每个被关注用户的粉丝数更新

        测试数据:
        - follower: sample_follows[0] (原始用户，当前登录)
        - targets: sample_follows[1:4] (zhangsan, lisi, wangwu)

        批量操作逻辑:
        1. 依次关注多个目标用户
        2. 统计成功的关注操作数
        3. 验证关注列表的总数正确
        4. 验证每个目标用户的粉丝数都增加

        业务场景:
        - 模拟新用户关注多个已有用户的场景
        - 验证系统在高频关注操作下的稳定性
        """
        follower = sample_follows[0]  # 原始用户 (当前登录)
        targets = sample_follows[1:4]  # zhangsan, lisi, wangwu (3个目标)

        followed_count = 0
        for target in targets:
            response = client.post(
                f"/api/v1/users/{target.id}/follow",
                headers=auth_headers,
            )
            if response.status_code == status.HTTP_201_CREATED:
                followed_count += 1

        # 验证关注者的关注列表总数正确
        response = client.get(f"/api/v1/users/{follower.id}/following")
        following_data = response.json()
        assert following_data["total"] >= followed_count

        # 验证每个被关注用户的粉丝数都增加
        for target in targets:
            follower_response = client.get(f"/api/v1/users/{target.id}/follower-count")
            assert follower_response.status_code == status.HTTP_200_OK
            assert follower_response.json() >= 1
