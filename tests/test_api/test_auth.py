"""
测试认证 API 端点

测试覆盖:
- 用户注册 API
- 用户登录 API
- 获取当前用户信息 API
- 各种错误场景 (400, 401, 409)
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.schemas.user import UserCreate


@pytest.fixture
def test_user_data() -> dict:
    """API 测试用户数据（包含明文密码）"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#",
        "nickname": "测试用户",
    }


class TestUserRegister:
    """测试用户注册 API"""

    def test_register_success(
        self, session: Session, client: TestClient, test_user_data: dict
    ):
        """测试成功注册新用户"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        # 验证响应状态码
        assert response.status_code == status.HTTP_201_CREATED

        # 验证响应数据
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["nickname"] == test_user_data["nickname"]
        assert "password" not in data
        assert "id" in data

        # 验证数据库
        db_user = crud_user.get_user_by_email(session, email=test_user_data["email"])
        assert db_user is not None
        assert db_user.username == test_user_data["username"]

    def test_register_duplicate_email(
        self, client: TestClient, session: Session, test_user_data: dict
    ):
        """测试注册重复邮箱 - 应该返回 409"""
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "邮箱已被注册" in response.json()["detail"]

    def test_register_duplicate_username(
        self, client: TestClient, session: Session, test_user_data: dict
    ):
        """测试注册重复用户名 - 应该返回 409"""
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        new_data = test_user_data.copy()
        new_data["email"] = "different@example.com"
        response = client.post("/api/v1/auth/register", json=new_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "用户名已被使用" in response.json()["detail"]

    # 添加无效数据测试
    # 测试场景:
    # 1. 邮箱格式错误 - 应该返回 422 (Pydantic 验证错误)
    # 2. 密码太短 - 应该返回 422
    # 3. 缺少必填字段 - 应该返回 422
    def test_register_invalid_email(self, client: TestClient, test_user_data: dict):
        """测试无效邮箱格式 - 应该返回 422"""
        # 修改 test_user_data 的 email 为无效格式（例如 "invalid-email"）
        user = test_user_data.copy()
        user["email"] = "invalid-email"
        # 发送 POST 请求到 /api/v1/auth/register
        response = client.post("/api/v1/auth/register", json=user)
        # 验证状态码是 status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # 验证响应中包含邮箱验证错误信息
        assert (
            response.json()["detail"][0]["msg"]
            == "value is not a valid email address: "
            "An email address must have an @-sign."
        )

    def test_register_password_too_short(
        self, client: TestClient, test_user_data: dict
    ):
        """测试密码太短 - 应该返回 422"""
        # 修改 test_user_data 的 password 为太短的密码（例如 "123"）
        user = test_user_data.copy()
        user["password"] = "123"
        # 发送 POST 请求
        response = client.post("/api/v1/auth/register", json=user)

        # 验证状态码是 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # 验证错误信息提到密码长度
        assert (
            response.json()["detail"][0]["msg"]
            == "String should have at least 8 characters"
        )

    def test_register_missing_required_field(
        self, client: TestClient, test_user_data: dict
    ):
        """测试缺少必填字段 - 应该返回 422"""
        # 复制 test_user_data 并删除 username 字段
        user = test_user_data.copy()
        del user["username"]
        # 发送 POST 请求
        response = client.post("/api/v1/auth/register", json=user)

        # 发送请求并验证 422 状态码
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # 验证错误信息
        assert response.json()["detail"][0]["msg"] == "Field required"


class TestUserLogin:
    """测试用户登录 API"""

    def test_login_success(
        self, client: TestClient, session: Session, test_user_data: dict
    ):
        """测试成功登录"""
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_email(
        self, client: TestClient, session: Session, test_user_data: dict
    ):
        """测试使用邮箱登录"""
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    # 添加登录失败测试
    # 测试场景:
    # 1. 错误的密码 - 应该返回 401 UNAUTHORIZED
    # 2. 不存在的用户 - 应该返回 401
    # 3. 验证错误信息包含 "用户名或密码错误"
    # 4. 验证响应头包含 "WWW-Authenticate": "Bearer"
    def test_login_wrong_password(
        self, client: TestClient, session: Session, test_user_data: dict
    ):
        """测试错误密码登录 - 应该返回 401"""
        # 先使用 crud_user.create_user() 创建用户
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        # 使用错误的密码登录（例如 "WrongPassword123"）
        response = client.post(
            url="/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": "WrongPassword123",
            },
        )

        # 验证返回 401 状态码
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 验证错误信息包含 "用户名或密码错误"
        assert "用户名或密码错误" in response.json()["detail"]

        # 验证响应头包含 "WWW-Authenticate"
        assert "WWW-Authenticate" in response.headers

    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在的用户登录 - 应该返回 401"""
        # 直接使用不存在的用户名登录（不创建用户）
        response = client.post(
            url="/api/v1/auth/login",
            data={"username": "non_existent_user", "password": "Password123!"},
        )
        # 验证返回 401 状态码
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # 验证错误信息
        assert "用户名或密码错误" in response.json()["detail"]


class TestGetCurrentUser:
    """测试获取当前用户信息 API"""

    @pytest.fixture
    def auth_headers(
        self, client: TestClient, session: Session, test_user_data: dict
    ) -> dict:
        """创建用户并返回认证 headers"""
        crud_user.create_user(session, user_in=UserCreate(**test_user_data))

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_get_me_success(
        self, client: TestClient, auth_headers: dict, test_user_data: dict
    ):
        """测试成功获取当前用户信息"""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]

    def test_get_me_without_token(self, client: TestClient):
        """测试未提供 token - 应该返回 401"""
        response = client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 添加更多认证失败测试
    # 测试场景:
    # 1. 无效的 token (篡改的字符串) - 应该返回 401
    # 2. 格式错误的 Authorization header (例如缺少 "Bearer " 前缀) - 应该返回 401
    #
    # 提示:
    # - 无效 token: headers={"Authorization": "Bearer invalid_token_string"}
    # - 错误格式: headers={"Authorization": "invalid_format"}
    # 验证状态码和错误信息

    def test_get_me_invalid_token(self, client: TestClient):
        """测试无效 token - 应该返回 401"""
        # 创建一个无效的 token（随便写一个字符串）
        # 发送 GET 请求到 /api/v1/users/me，带上无效 token
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_fake_token_12345"},
        )
        # 验证返回 401 状态码
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]

    def test_get_me_malformed_auth_header(self, client: TestClient):
        """测试格式错误的 Authorization header - 应该返回 401"""
        # 创建错误格式的 header（缺少 "Bearer " 前缀）
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": "some_token_without_bearer"}
        )
        # 发送请求并验证 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"
