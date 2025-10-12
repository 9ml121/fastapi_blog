"""
测试用户资料管理 API 端点

测试覆盖：
- GET /users/me - 获取当前用户资料
- PATCH /users/me - 更新当前用户资料
- PUT /users/me/password - 修改密码

测试策略：
1. 测试数据四象限：正常、边界、异常、极端
2. 逻辑分支覆盖：每个 if-else 都有测试
3. 安全验证：认证、权限、密码验证
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate


class TestGetCurrentUserProfile:
    """测试获取当前用户资料 API (GET /users/me)"""

    url = "/api/v1/users/me"

    def test_get_profile_success(
        self, client: TestClient, auth_headers: dict, sample_user: User
    ):
        """✅ 正常数据：成功获取当前用户资料"""
        response = client.get(self.url, headers=auth_headers)

        # 验证状态码
        assert response.status_code == status.HTTP_200_OK

        # 验证响应数据
        data = response.json()
        assert data["id"] == str(sample_user.id)
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
        assert data["nickname"] == sample_user.nickname

        # 验证敏感字段不返回
        assert "password_hash" not in data
        assert "password" not in data

    def test_get_profile_without_token(self, client: TestClient):
        """✅ 异常数据：未提供 token - 应该返回 401"""
        response = client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    def test_get_profile_invalid_token(self, client: TestClient):
        """✅ 异常数据：无效的 token - 应该返回 401"""
        headers = {"Authorization": "Bearer invalid_token_string"}
        response = client.get(self.url, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]


class TestUpdateCurrentUserProfile:
    """测试更新当前用户资料 API (PATCH /users/me)

    测试重点：
    1. PATCH 语义：支持部分更新（只传入要修改的字段）
    2. 邮箱去重：不能使用已被占用的邮箱
    3. 数据验证：Pydantic schema 验证
    """

    url = "/api/v1/users/me"

    def test_update_nickname_success(
        self, client: TestClient, auth_headers: dict, sample_user: User
    ):
        """✅ 正常数据：成功更新昵称"""
        new_nickname = "新昵称"
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"nickname": new_nickname},
        )

        # 验证状态码
        assert response.status_code == status.HTTP_200_OK

        # 验证响应数据
        data = response.json()
        assert data["nickname"] == new_nickname

        # 验证其他字段未被修改
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email

    def test_update_email_success(
        self, client: TestClient, auth_headers: dict, sample_user: User
    ):
        """✅ 正常数据：成功更新邮箱（新邮箱未被占用）"""
        new_email = "newemail@example.com"
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"email": new_email},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == new_email

    def test_update_multiple_fields(self, client: TestClient, auth_headers: dict):
        """✅ 正常数据：同时更新多个字段"""
        update_data = {
            "nickname": "多字段更新",
            "email": "multiple_update@example.com",
        }
        response = client.patch(
            self.url,
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nickname"] == update_data["nickname"]
        assert data["email"] == update_data["email"]

    def test_update_partial_fields_only(
        self, client: TestClient, auth_headers: dict, sample_user: User
    ):
        """✅ 边界数据：PATCH 语义验证 - 只传入一个字段，其他字段不变"""
        original_email = sample_user.email

        # 只更新 nickname
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"nickname": "只改昵称"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证只有 nickname 被更新
        assert data["nickname"] == "只改昵称"
        # 验证其他字段保持不变
        assert data["email"] == original_email

    def test_update_empty_nickname(self, client: TestClient, auth_headers: dict):
        """✅ 边界数据：空字符串昵称 - 应该返回 422（Schema 限制 min_length=1）"""
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"nickname": ""},
        )

        # Schema 定义了 min_length=1，空字符串会被拒绝
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_duplicate_email(
        self, client: TestClient, session: Session, auth_headers: dict
    ):
        """✅ 异常数据：邮箱冲突 - 新邮箱已被其他用户占用"""
        # 创建另一个用户
        other_user = crud_user.create_user(
            session,
            user_in=UserCreate(
                username="otheruser",
                email="other@example.com",
                password="Password123!",
            ),
        )

        # 尝试将当前用户的邮箱改为 other_user 的邮箱
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"email": other_user.email},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "邮箱已被其他用户占用" in response.json()["detail"]

    def test_update_invalid_email_format(self, client: TestClient, auth_headers: dict):
        """✅ 异常数据：无效的邮箱格式 - 应该返回 422"""
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"email": "invalid-email-format"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_without_authentication(self, client: TestClient):
        """✅ 异常数据：未认证用户 - 应该返回 401"""
        response = client.patch(
            self.url,
            json={"nickname": "应该失败"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """测试修改密码 API (PUT /users/me/password)

    测试重点：
    1. 安全验证：必须提供正确的旧密码
    2. 密码强度：新密码必须符合要求（≥8字符）
    3. 密码生效：修改后能用新密码登录
    """

    url = "/api/v1/users/me/password"

    @pytest.fixture
    def auth_headers_with_password(
        self, client: TestClient, sample_user_with_password: tuple
    ) -> tuple[dict, str]:
        """生成认证 headers 和明文密码

        Returns:
            tuple[dict, str]: (认证headers, 明文密码)
        """
        from app.core.security import create_access_token

        user, plain_password = sample_user_with_password
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        return headers, plain_password

    # TODO(human): 完成修改密码的测试用例
    #
    # 📝 重要提示：
    # - 使用 `auth_headers_with_password` fixture 获取认证和密码
    # - 它返回 (headers, plain_password) 元组
    # - plain_password 是 "TestPassword123!"
    #
    # 使用方式：
    # def test_xxx(self, client, auth_headers_with_password, session):
    #     headers, old_password = auth_headers_with_password
    #     # 然后使用 old_password 和 headers
    #
    # 编写以下 6 个测试场景：
    #
    # 1. ✅ 正常数据：test_change_password_success
    #    - 提供正确的旧密码和有效的新密码
    #    - json={"old_password": old_password, "new_password": "NewPassword123!"}
    #    - 验证返回 200 和 {"message": "密码修改成功"}
    def test_change_password_success(
        self, client: TestClient, auth_headers_with_password: tuple[dict, str]
    ):
        """✅ 正常数据：成功修改密码"""
        headers, old_password = auth_headers_with_password
        response = client.put(
            self.url,
            headers=headers,
            json={"old_password": old_password, "new_password": "NewPassword123!"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "密码修改成功"

    # 2. ✅ 异常数据：test_change_password_wrong_old_password
    #    - 提供错误的旧密码
    #    - json={"old_password": "WrongPassword!", "new_password": "NewPassword123!"}
    #    - 验证返回 400 和错误信息包含"旧密码错误"
    def test_change_password_wrong_old_password(
        self, client: TestClient, auth_headers_with_password: tuple[dict, str]
    ):
        """✅ 异常数据：提供错误的旧密码"""
        headers, old_password = auth_headers_with_password
        response = client.put(
            self.url,
            headers=headers,
            json={"old_password": "WrongPassword!", "new_password": "NewPassword123!"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "旧密码错误" in response.json()["detail"]

    # 3. ✅ 边界数据：test_change_password_too_short
    #    - 新密码太短（例如 "123"）
    #    - 验证返回 422（Pydantic 验证失败）
    def test_change_password_too_short(
        self, client: TestClient, auth_headers_with_password: tuple[dict, str]
    ):
        """✅ 边界数据：新密码太短"""
        headers, old_password = auth_headers_with_password
        response = client.put(
            self.url,
            headers=headers,
            json={"old_password": old_password, "new_password": "123!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # print(response.json())
        assert (
            "String should have at least 8 characters"
            in response.json()["detail"][0]["msg"]
        )

    # 4. ✅ 边界数据：test_change_password_same_as_old
    #    - 新旧密码相同
    #    - json={"old_password": old_password, "new_password": old_password}
    #    - 验证返回 200（允许，这是业务决策）
    def test_change_password_same_as_old(
        self, client: TestClient, auth_headers_with_password: tuple[dict, str]
    ):
        """✅ 边界数据：新旧密码相同"""
        headers, old_password = auth_headers_with_password
        response = client.put(
            self.url,
            headers=headers,
            json={"old_password": old_password, "new_password": old_password},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "密码修改成功"

    # 5. ✅ 异常数据：test_change_password_without_authentication
    #    - 不提供 token（不使用 headers）
    #    - 验证返回 401
    def test_change_password_without_authentication(self, client: TestClient):
        """✅ 异常数据：不提供 token"""
        response = client.put(
            self.url,
            json={"old_password": "OldPassword123!", "new_password": "NewPassword123!"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 6. ✅ 极端数据：test_change_password_can_login_with_new_password
    #    - 修改密码后，验证能用新密码登录
    #    - 步骤：
    #      a. 调用修改密码 API
    #      b. 从 sample_user_with_password 获取用户名
    #      c. 调用 POST /api/v1/auth/login，使用新密码
    #      d. 验证登录成功（返回 access_token）
    def test_change_password_can_login_with_new_password(
        self,
        client: TestClient,
        sample_user_with_password: tuple[User, str],
        auth_headers_with_password: tuple[dict, str],
    ):
        """✅ 极端数据：修改密码后，验证能用新密码登录"""
        # a. 调用修改密码 API
        headers, old_password = auth_headers_with_password
        response = client.put(
            self.url,
            headers=headers,
            json={"old_password": old_password, "new_password": "NewPassword123!"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "密码修改成功"

        # b. 从 sample_user_with_password 获取用户名
        user, _ = sample_user_with_password

        # c. 调用 POST /api/v1/auth/login，使用新密码
        response = client.post(
            "/api/v1/auth/login",
            data={"username": user.username, "password": "NewPassword123!"},
        )

        # d. 验证登录成功（返回 access_token）
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
