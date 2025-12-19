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

from app.crud import user as user_crud
from app.models.user import User, UserRole
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

        # HTTPException 现在通过我们的处理器返回统一格式
        error_data = response.json()["error"]
        assert error_data["code"] == "HTTP_ERROR"
        assert error_data["message"] == "Not authenticated"

    def test_get_profile_invalid_token(self, client: TestClient):
        """✅ 异常数据：无效的 token - 应该返回 401"""
        headers = {"Authorization": "Bearer invalid_token_string"}
        response = client.get(self.url, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # 现在使用新格式（自定义异常处理器）
        error_data = response.json()["error"]
        assert error_data["code"] == "UNAUTHORIZED"
        assert "Could not validate credentials" in error_data["message"]


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
        """✅ 正常数据：成功更新昵称，其他字段未被修改"""
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
        update_data = {"nickname": "多字段更新", "email": "multiple_update@example.com"}
        response = client.patch(
            self.url,
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nickname"] == update_data["nickname"]
        assert data["email"] == update_data["email"]

    def test_update_not_defined_fields(
        self, client: TestClient, auth_headers: dict, sample_user: User
    ):
        """✅ 异常数据：尝试修改更新模型未定义的字段，应该返回 422"""
        # 尝试更新 usename, 接口会报错
        response = client.patch(
            self.url,
            headers=auth_headers,
            json={"username": "new_username"},
        )

        print(response.json())
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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
        other_user = user_crud.create_user(
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
        error_data = response.json()["error"]
        assert error_data["code"] == "EMAIL_ALREADY_EXISTS"
        assert "邮箱已被注册" in error_data["message"]

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
        error_data = response.json()["error"]
        assert error_data["code"] == "INVALID_PASSWORD"
        assert "旧密码错误" in error_data["message"]

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
        # 验证响应格式（现在通过全局异常处理器处理）
        error_data = response.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "请求数据格式错误" in error_data["message"]
        # 验证 details 中包含密码长度错误
        details = error_data["details"]
        assert any("new_password" in str(detail.get("loc", [])) for detail in details)

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

    def test_change_password_without_authentication(self, client: TestClient):
        """✅ 异常数据：不提供 token"""
        response = client.put(
            self.url,
            json={"old_password": "OldPassword123!", "new_password": "NewPassword123!"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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


# ================== 管理员功能测试 ==================


@pytest.fixture
def admin_user(session: Session) -> User:
    """创建管理员用户 fixture"""
    admin_in = UserCreate(
        email="admin@example.com",
        password="AdminPassword123!",
        username="admin",
        nickname="管理员",
    )
    admin = user_crud.create_user(db=session, user_in=admin_in)
    admin.role = UserRole.ADMIN
    session.commit()
    return admin


@pytest.fixture
def admin_headers(client: TestClient, admin_user: User) -> dict[str, str]:
    """管理员认证 headers fixture"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "AdminPassword123!"},
    )
    admin_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def normal_user(session: Session) -> User:
    """创建普通用户 fixture"""
    user_in = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        username="testuser",
        nickname="测试用户",
    )
    return user_crud.create_user(db=session, user_in=user_in)


@pytest.fixture
def another_user(session: Session) -> User:
    """创建第二个普通用户 fixture（用于权限测试）"""
    user_in = UserCreate(
        email="another@example.com",
        password="TestPassword123!",
        username="anotheruser",
        nickname="另一个用户",
    )
    return user_crud.create_user(db=session, user_in=user_in)


@pytest.fixture
def normal_user_headers(client: TestClient, normal_user: User) -> dict[str, str]:
    """普通用户认证 headers fixture"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": normal_user.username, "password": "TestPassword123!"},
    )
    user_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {user_token}"}


class TestUpdateUserByAdmin:
    """测试管理员更新用户信息功能"""

    # ================== 正常数据测试 ==================

    def test_admin_update_user_success(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 正常数据：管理员成功更新用户信息"""
        # 管理员更新用户信息
        update_data = {"nickname": "管理员更新的昵称", "is_active": False}
        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证更新成功
        assert response.status_code == status.HTTP_200_OK
        updated_user = response.json()
        assert updated_user["nickname"] == "管理员更新的昵称"
        assert updated_user["is_active"] is False

    # ================== 异常数据测试 ==================

    def test_admin_update_nonexistent_user(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """✅ 异常数据：管理员更新不存在的用户"""
        # 尝试更新不存在的用户
        update_data = {"nickname": "新昵称"}
        fake_user_id = "12345678-1234-5678-9abc-123456789abc"

        response = client.patch(
            f"/api/v1/users/{fake_user_id}", json=update_data, headers=admin_headers
        )

        # 验证返回用户不存在错误
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()["error"]
        assert error_data["code"] == "RESOURCE_NOT_FOUND"
        assert "用户不存在" in error_data["message"]

    def test_normal_user_update_forbidden(
        self,
        client: TestClient,
        normal_user_headers: dict[str, str],
        another_user: User,
    ):
        """✅ 异常数据：普通用户尝试更新其他用户应该被拒绝"""
        # 普通用户尝试更新其他用户（应该被拒绝）
        update_data = {"nickname": "非法更新"}

        response = client.patch(
            f"/api/v1/users/{another_user.id}",
            json=update_data,
            headers=normal_user_headers,
        )

        # 验证权限被拒绝
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_data = response.json()["error"]
        assert error_data["code"] == "HTTP_ERROR"
        assert "doesn't have enough privileges" in error_data["message"]

    # ================== 正常数据测试（续） ==================

    def test_admin_update_user_password(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 正常数据：管理员重置用户密码"""
        new_password = "NewPassword123!"

        # 管理员重置用户密码
        update_data = {"password": new_password}
        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证密码重置成功
        assert response.status_code == status.HTTP_200_OK

        # 用户可以用新密码登录
        response = client.post(
            "/api/v1/auth/login",
            data={"username": normal_user.username, "password": new_password},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_admin_update_user_without_auth(self, client: TestClient):
        """✅ 异常数据：未认证用户尝试管理员操作"""
        update_data = {"nickname": "非法更新"}
        fake_user_id = "12345678-1234-5678-9abc-123456789abc"

        response = client.patch(f"/api/v1/users/{fake_user_id}", json=update_data)

        # 验证未认证
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error = response.json()
        assert error["error"]["code"] == "HTTP_ERROR"
        assert error["error"]["message"] == "Not authenticated"

    # ================== 边界数据测试 ==================

    def test_admin_update_user_with_empty_nickname(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 边界数据：管理员更新用户昵称为空字符串"""
        update_data = {"nickname": ""}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # Schema 定义了 min_length=1，空字符串会被拒绝
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "请求数据格式错误" in error_data["message"]

    def test_admin_update_user_with_minimum_password(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 边界数据：管理员重置密码为最小有效复杂度密码"""
        # 8位包含字母和数字的最小复杂度密码
        update_data = {"password": "Password1"}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证更新成功
        assert response.status_code == status.HTTP_200_OK

        # 验证可以用新密码登录
        response = client.post(
            "/api/v1/auth/login",
            data={"username": normal_user.username, "password": "Password1"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_update_user_with_simple_password(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 边界数据：管理员尝试重置简单密码应该被拒绝"""
        # 8位纯数字密码（缺少字母）
        update_data = {"password": "12345678"}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证简单密码被拒绝
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "请求数据格式错误" in error_data["message"]

        # 验证具体的密码错误信息
        details = error_data["details"]
        has_letter_error = any(
            "密码必须包含至少一个字母" in str(detail.get("msg", ""))
            for detail in details
        )
        assert has_letter_error

    def test_admin_update_user_with_short_password(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 边界数据：管理员尝试重置过短密码应该被拒绝"""
        # 6位复杂度密码但长度不足
        update_data = {"password": "Pass12"}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证过短密码被拒绝
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "请求数据格式错误" in error_data["message"]

        # 验证具体的密码错误信息
        details = error_data["details"]
        has_length_error = any(
            "at least 8 characters" in str(detail.get("msg", "")) for detail in details
        )
        assert has_length_error

    # ================== 极端数据测试 ==================

    def test_admin_update_user_with_long_nickname(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 极端数据：管理员更新用户昵称为最大长度字符串"""
        # 50 字符的最大长度昵称（根据 Schema max_length=50）
        max_nickname = "a" * 50
        update_data = {"nickname": max_nickname}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证更新成功（最大长度应该被接受）
        assert response.status_code == status.HTTP_200_OK
        updated_user = response.json()
        assert updated_user["nickname"] == max_nickname

    def test_admin_update_user_with_overlimit_nickname(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 极端数据：管理员更新用户昵称为超限字符串"""
        # 51 字符的超长昵称（超过 Schema max_length=50）
        overlimit_nickname = "a" * 51
        update_data = {"nickname": overlimit_nickname}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证超长字符串被拒绝
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "请求数据格式错误" in error_data["message"]

    def test_admin_update_user_with_special_chars(
        self, client: TestClient, admin_headers: dict[str, str], normal_user: User
    ):
        """✅ 极端数据：管理员更新用户昵称包含特殊字符"""
        special_nickname = "测试用户🎉@#$%^&*()_+-=[]{}|;':\",./<>?"
        update_data = {"nickname": special_nickname}

        response = client.patch(
            f"/api/v1/users/{normal_user.id}", json=update_data, headers=admin_headers
        )

        # 验证更新成功
        assert response.status_code == status.HTTP_200_OK
        updated_user = response.json()
        assert updated_user["nickname"] == special_nickname
