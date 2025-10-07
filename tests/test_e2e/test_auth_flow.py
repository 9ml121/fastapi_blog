"""
端到端测试 - 认证流程

测试覆盖：
1. 新用户完整流程（注册 → 登录 → 访问受保护端点）
2. 权限控制（普通用户 vs 管理员）
3. Token 生命周期（有效 token、过期 token）
"""

from datetime import timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.security import create_access_token
from app.schemas.user import UserCreate


@pytest.fixture
def test_user_data() -> dict[str, str]:
    """API 测试用户数据（包含明文密码）"""
    return {"username": "newuser", "email": "newuser@example.com", "password": "SecurePass123!", "nickname": "New User"}


class TestAuthenticationFlow:
    """测试完整的认证流程"""

    def test_new_user_complete_journey(self, client: TestClient, test_user_data: dict[str, str]):
        """
        测试新用户从注册到使用的完整旅程

        用户旅程：
        1. 用户访问网站，注册新账号
        2. 使用新账号登录，获取 JWT token
        3. 使用 token 访问受保护的 /me 端点
        4. 验证返回的用户信息与注册时一致
        """
        # Step 1: 注册新用户

        register_response = client.post("/api/v1/auth/register", json=test_user_data)

        # 验证注册成功
        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()
        assert user_data["username"] == test_user_data["username"]
        assert user_data["email"] == test_user_data["email"]
        assert "password" not in user_data  # 密码不应该返回

        # Step 2: 使用新账号登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        # 验证登录成功并获取 token
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        access_token = token_data["access_token"]

        # Step 3: 使用 token 访问受保护端点
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # 验证成功获取用户信息
        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()

        # Step 4: 验证用户信息一致性（注册 → 登录 → /me）
        assert me_data["username"] == test_user_data["username"]
        assert me_data["email"] == test_user_data["email"]
        assert me_data["nickname"] == test_user_data["nickname"]
        assert me_data["id"] == user_data["id"]  # ID 应该与注册时返回的一致

    def test_login_with_email_then_access_protected_endpoint(self, client: TestClient, test_user_data: dict[str, str]):
        """
        测试使用邮箱登录后访问受保护端点

        流程：
        1. 注册用户
        2. 使用邮箱（而非用户名）登录
        3. 用 token 访问 /me
        """
        # 1. 先注册一个用户（使用 client.post("/api/v1/auth/register", ...)）
        register_response = client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # 2. 使用邮箱登录（username 字段传邮箱）
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        # 3. 验证能成功获取 token
        assert "access_token" in login_response.json()
        access_token = login_response.json()["access_token"]

        # 4. 用 token 访问 /me，验证返回正确的用户信息
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == test_user_data["username"]
        assert me_response.json()["email"] == test_user_data["email"]
        assert me_response.json()["nickname"] == test_user_data["nickname"]


class TestPermissionControl:
    """测试权限控制"""

    @pytest.fixture
    def normal_user_token(self, client: TestClient) -> str:
        """创建普通用户并返回其 token"""
        # 注册普通用户
        user_data = {
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "Pass123!",
            "nickname": "Normal User",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 登录获取 token
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user_data["username"], "password": user_data["password"]},
        )
        return login_response.json()["access_token"]

    @pytest.fixture
    def admin_user_token(self, client: TestClient, session: Session) -> str:
        """创建管理员用户并返回其 token"""
        # 1. 使用 crud_user.create_user() 创建用户
        email = "test@example.com"
        password = "TestPassword123"
        username = "testuser"
        user_in = UserCreate(email=email, password=password, username=username)

        admin_user = crud.user.create_user(session, user_in=user_in)
        # 2. 调用 user.promote_to_admin() 提升为管理员
        admin_user.promote_to_admin()
        # 3. session.commit() 保存
        session.add(admin_user)
        session.commit()
        # 4. 使用 create_access_token() 生成 token
        token = create_access_token(data={"sub": str(admin_user.id)})
        # 5. 返回 token 字符串
        return token

    def test_normal_user_cannot_access_admin_endpoint(self, client: TestClient, normal_user_token: str):
        """
        测试普通用户无法访问管理员端点

        预期：返回 403 Forbidden

        注意：由于我们还没实现真正的管理员端点（Phase 4 才会添加），
        这个测试暂时验证普通用户可以访问 /me 并且角色是 user
        """
        # 临时测试：验证普通用户可以访问自己的信息
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {normal_user_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "user"  # 验证角色是普通用户

    def test_admin_user_can_access_admin_endpoint(self, client: TestClient, admin_user_token: str):
        """
        测试管理员可以访问管理员端点

        预期：返回 200 OK

        注意：由于我们还没实现真正的管理员端点（Phase 4 才会添加），
        这个测试暂时验证管理员可以访问 /me 并且角色是 admin
        """
        # 临时测试：验证管理员可以访问自己的信息，并且角色是 admin
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_user_token}"})

        # 验证返回 200 状态码
        assert response.status_code == status.HTTP_200_OK

        # 验证用户角色是 admin
        assert response.json()["role"] == "admin"


class TestTokenLifecycle:
    """测试 Token 生命周期"""

    def test_expired_token_rejected(self, client: TestClient, session: Session, sample_user):
        """
        测试过期的 token 被拒绝

        流程：
        1. 创建一个已过期的 token（expires_delta=-1 秒）
        2. 使用过期 token 访问 /me
        3. 验证返回 401 Unauthorized
        """
        # 1. 创建一个已过期的 token（-1 秒表示立即过期）
        expired_token = create_access_token(
            data={"sub": str(sample_user.id)},
            expires_delta=timedelta(seconds=-1),
        )

        # 2. 使用过期 token 访问受保护端点
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

        # 3. 验证返回 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_valid_token_with_custom_expiration(self, client: TestClient, session: Session, sample_user):
        """
        测试自定义过期时间的有效 token

        流程：
        1. 创建一个 10 秒后过期的 token
        2. 立即使用，应该成功
        3. 等待 11 秒（模拟过期）
        4. 再次使用，应该失败
        """
        # 创建 10 秒后过期的 token
        short_lived_token = create_access_token(
            data={"sub": str(sample_user.id)},
            expires_delta=timedelta(seconds=10),
        )

        # 立即使用，应该成功
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {short_lived_token}"})
        assert response.status_code == status.HTTP_200_OK

        # 注意：这个测试需要等待 11 秒，在实际开发中可能太慢
        # 在 CI/CD 中可以跳过这个测试（使用 @pytest.mark.slow）
        # 这里我们只验证立即使用是成功的，过期测试在上面的 test_expired_token_rejected 中完成
