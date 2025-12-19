"""
Phase 5.2 基础设施测试

测试内容：
1. CORS 中间件配置
2. 自定义异常类
3. 全局异常处理器
4. 端点重构后的异常格式（回归测试）

测试策略：
- CORS 测试：验证响应头
- 异常类测试：单元测试验证属性
- 异常处理器测试：触发异常验证响应格式
- 回归测试：确保现有端点返回新格式错误
"""

from pprint import pprint  # noqa: F401

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    UnauthorizedError,
    UsernameAlreadyExistsError,
)
from app.crud import user as user_crud
from app.schemas.user import UserCreate

# ============ 1. CORS 中间件测试 ============


def test_cors_preflight_request(client: TestClient):
    """测试 CORS 预检请求（OPTIONS 请求）

    验证点：
    1. 预检请求返回 200
    2. Access-Control-Allow-Origin 包含允许的域
    3. Access-Control-Allow-Credentials 为 true
    4. Access-Control-Allow-Methods 包含所有方法
    """
    # 模拟浏览器发起的预检请求
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    # 验证状态码
    assert response.status_code == status.HTTP_200_OK

    # 验证 CORS 响应头
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-methods" in response.headers


def test_cors_actual_request(client: TestClient):
    """测试 CORS 实际请求（带 Origin 头的 POST 请求）

    验证点：
    1. 实际请求正常处理
    2. 响应包含 Access-Control-Allow-Origin
    3. 响应包含 Access-Control-Allow-Credentials
    """
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
        },
        headers={"Origin": "http://localhost:3000"},
    )

    # 验证 CORS 响应头（无论业务逻辑成功与否，CORS 头都应该存在）
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers


# ============ 2. 自定义异常类测试 ============


def test_email_already_exists_error():
    """测试 EmailAlreadyExistsError 异常属性

    测试数据四象限：
    - 正常数据：标准邮箱格式
    """
    email = "test@example.com"
    exc = EmailAlreadyExistsError(email=email)

    # 验证异常属性
    assert exc.code == "EMAIL_ALREADY_EXISTS"
    assert exc.message == "邮箱已被注册"
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.details == {"field": "email", "value": email}


def test_username_already_exists_error():
    """测试 UsernameAlreadyExistsError 异常属性

    测试数据四象限：
    - 正常数据：标准用户名
    """
    username = "testuser"
    exc = UsernameAlreadyExistsError(username=username)

    assert exc.code == "USERNAME_ALREADY_EXISTS"
    assert exc.message == "用户名已被使用"
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.details == {"field": "username", "value": username}


def test_invalid_credentials_error():
    """测试 InvalidCredentialsError 异常属性

    安全考虑：不暴露具体是用户名还是密码错误
    """
    exc = InvalidCredentialsError()

    assert exc.code == "INVALID_CREDENTIALS"
    assert exc.message == "用户名或密码错误"
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.details is None


def test_unauthorized_error():
    """测试 UnauthorizedError 异常属性

    场景：缺少或无效的认证凭据
    """
    exc = UnauthorizedError()

    assert exc.code == "UNAUTHORIZED"
    assert exc.message == "请先登录"
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED


def test_permission_denied_error():
    """测试 PermissionDeniedError 异常属性

    场景：已认证但无权限（403 vs 401）
    """
    message = "权限不足"
    exc = PermissionDeniedError(message=message)

    assert exc.code == "PERMISSION_DENIED"
    assert exc.message == message
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.details is None


def test_resource_not_found_error():
    """测试 ResourceNotFoundError 异常属性

    场景：请求不存在的资源（404）
    """
    resource = "文章"
    exc = ResourceNotFoundError(resource=resource)

    assert exc.code == "RESOURCE_NOT_FOUND"
    assert exc.message == f"{resource}不存在"
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.details is None


def test_resource_conflict_error():
    """测试 ResourceConflictError 异常属性

    场景：资源冲突（如并发修改、状态冲突）
    """
    message = "文章已发布，无法修改"
    exc = ResourceConflictError(message=message)

    assert exc.code == "RESOURCE_CONFLICT"
    assert exc.message == message
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.details is None


# ============ 3. 全局异常处理器测试 ============


def test_app_error_handler(client: TestClient, session: Session):
    """测试 AppError 异常处理器

    验证点：
    1. 返回统一的 JSON 格式
    2. status_code 正确
    3. error.code、error.message、error.details 正确

    测试数据：复用已存在的用户触发 EmailAlreadyExistsError
    """
    # 准备测试数据：创建一个用户
    user_data = UserCreate(
        username="existing_user",
        email="existing@example.com",
        password="SecurePass123!",
    )
    user_crud.create_user(session, user_in=user_data)

    # 尝试用相同邮箱注册，触发 EmailAlreadyExistsError
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "existing@example.com",
            "password": "AnotherPass123!",
        },
    )

    # 验证响应格式
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    error = response.json()["error"]
    assert error["code"] == "EMAIL_ALREADY_EXISTS"
    assert error["message"] == "邮箱已被注册"
    assert "details" in error
    assert error["details"]["field"] == "email"
    assert error["details"]["value"] == "existing@example.com"


def test_validation_error_handler(client: TestClient):
    """测试 RequestValidationError 处理器（422）

    验证点：
    1. Pydantic 验证失败返回统一格式
    2. details 包含详细的验证错误信息

    测试数据四象限：
    - 异常数据：邮箱格式错误
    """
    # 发送邮箱格式错误的请求
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",  # 错误的邮箱格式
            "password": "SecurePass123!",
        },
    )

    # 验证响应格式
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "error" in response.json()
    error = response.json()["error"]
    # pprint(error)
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "请求数据格式错误"
    assert "details" in error
    assert isinstance(error["details"], list)
    # Pydantic 错误详情应该包含字段位置和错误类型
    assert len(error["details"]) > 0


def test_validation_error_missing_field(client: TestClient):
    """测试缺少必填字段的验证错误

    测试数据四象限：
    - 异常数据：缺少必填字段
    """
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            # 缺少 email 和 password
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()["error"]
    # pprint(error)
    assert error["code"] == "VALIDATION_ERROR"
    assert len(error["details"]) >= 2  # 至少缺少 email 和 password 两个错误


# ============ 4. 端点重构回归测试 ============


def test_register_username_conflict_returns_new_format(client: TestClient):
    """测试注册时用户名冲突返回新格式错误

    回归测试：确保端点重构后行为正确
    """
    # 准备测试数据：先注册一个用户
    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "existinguser",
            "email": "user1@example.com",
            "password": "SecurePass123!",
        },
    )
    # 确保第一个注册成功
    assert first_response.status_code == 201

    # 尝试用相同用户名但不同邮箱注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "existinguser",
            "email": "different@example.com",
            "password": "AnotherPass123!",
        },
    )

    # 验证返回新的统一格式
    assert response.status_code == status.HTTP_409_CONFLICT
    error = response.json()["error"]
    assert error["code"] == "USERNAME_ALREADY_EXISTS"
    assert error["message"] == "用户名已被使用"
    assert error["details"]["field"] == "username"
    assert error["details"]["value"] == "existinguser"


def test_login_invalid_credentials_returns_new_format(client: TestClient):
    """测试登录失败返回新格式错误

    回归测试：确保端点重构后行为正确
    测试数据四象限：
    - 异常数据：错误的用户名/密码
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "WrongPass123!",
        },
    )

    # 验证返回新的统一格式
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()["error"]
    assert error["code"] == "INVALID_CREDENTIALS"
    assert error["message"] == "用户名或密码错误"


def test_update_profile_email_conflict_returns_new_format(client: TestClient):
    """测试更新资料时邮箱冲突返回新格式错误

    回归测试：确保端点重构后行为正确
    """
    # 注册第一个用户（当前用户）
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "currentuser",
            "email": "current@example.com",
            "password": "SecurePass123!",
        },
    )

    # 登录获取 token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "currentuser",
            "password": "SecurePass123!",
        },
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 注册第二个用户占用目标邮箱
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "otheruser",
            "email": "occupied@example.com",
            "password": "SecurePass123!",
        },
    )

    # 尝试更新当前用户的邮箱为已占用邮箱
    response = client.patch(
        "/api/v1/users/me",
        json={"email": "occupied@example.com"},
        headers=auth_headers,
    )

    # 验证返回新的统一格式
    assert response.status_code == status.HTTP_409_CONFLICT
    error = response.json()["error"]
    assert error["code"] == "EMAIL_ALREADY_EXISTS"
    assert error["message"] == "邮箱已被注册"


def test_change_password_invalid_old_password_returns_new_format(client: TestClient):
    """测试密码修改时旧密码错误返回新格式

    回归测试：确保端点重构后行为正确
    测试数据四象限：
    - 异常数据：错误的旧密码
    """
    # 注册用户
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "passworduser",
            "email": "password@example.com",
            "password": "OldPassword123!",
        },
    )

    # 登录获取 token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "passworduser",
            "password": "OldPassword123!",
        },
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 尝试用错误的旧密码修改密码
    response = client.put(
        "/api/v1/users/me/password",
        json={
            "old_password": "WrongOldPass123!",
            "new_password": "NewSecurePass123!",
        },
        headers=auth_headers,
    )

    # 验证返回新的统一格式
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()["error"]
    assert error["code"] == "INVALID_PASSWORD"
    assert error["message"] == "旧密码错误"
