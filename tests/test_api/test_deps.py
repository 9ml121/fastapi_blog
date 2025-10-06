from datetime import timedelta
import re

from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import create_access_token
from app.models.user import User

# 创建一个临时的 FastAPI 应用用于测试依赖项
app = FastAPI()


# 定义一个使用依赖项的测试端点
@app.get("/test-current-user")
def _(current_user: User = Depends(deps.get_current_user)):
    return current_user


@app.get("/test-active-user")
def _(current_user: User = Depends(deps.get_current_active_user)):
    return current_user


@app.get("/test-superuser")
def _(current_user: User = Depends(deps.get_current_superuser)):
    return current_user


client = TestClient(app)


def test_get_current_user_with_valid_token(session: Session, sample_user: User) -> None:
    """
    测试: 使用有效的 token 调用 get_current_user
    预期: 成功返回对应的用户
    """
    # 1. sample_user fixture 已经创建了一个用户
    user = sample_user

    # 2. 为该用户创建一个 token
    token = create_access_token(data={"sub": str(user.id)})

    # 3. 覆盖 get_db 依赖，使其使用测试数据库会话
    app.dependency_overrides[deps.get_db] = lambda: session

    # 4. 发送请求
    response = client.get("/test-current-user", headers={"Authorization": f"Bearer {token}"})

    # 5. 断言
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == str(user.id)
    assert response_data["email"] == user.email

    # 清理依赖覆盖
    app.dependency_overrides = {}


def test_get_current_user_with_invalid_token(session: Session) -> None:
    """
    测试: 使用无效的 token (签名错误)
    预期: 抛出 401 HTTPException
    """
    # 1. 覆盖 get_db 依赖
    app.dependency_overrides[deps.get_db] = lambda: session

    # 2. 发送请求
    response = client.get("/test-current-user", headers={"Authorization": "Bearer invalidtoken"})

    # 3. 断言
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]

    # 清理依赖覆盖
    app.dependency_overrides = {}


# ==================================
# 🧑‍💻 你的任务 (Your Task)
# ==================================


def test_get_current_user_with_expired_token(session: Session, sample_user: User) -> None:
    """
    测试: 使用已过期的 token
    预期: 抛出 401 HTTPException
    """
    # TODO: 在这里编写你的测试代码
    # 提示:
    # 1. sample_user fixture 已经提供了一个用户
    # 2. 创建一个已过期的 token
    token = create_access_token(data={"sub": str(sample_user.id)}, expires_delta=timedelta(seconds=-1))
    # 3. 覆盖 get_db 依赖
    app.dependency_overrides[deps.get_db] = lambda: session
    # 4. 发送请求到 /test-current-user
    response = client.get("/test-current-user", headers={"Authorization": f"Bearer {token}"})

    # 5. 断言 status_code 是否为 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 6. 清理依赖覆盖
    app.dependency_overrides = {}


def test_get_current_active_user_with_inactive_user(session: Session, sample_user: User) -> None:
    """
    测试: 使用一个被禁用用户的 token 调用 get_current_active_user
    预期: 抛出 400 HTTPException
    """
    # TODO: 在这里编写你的测试代码
    # 提示:
    # 1. 创建一个 is_active=False 的用户。你可以直接修改 sample_user 的属性并提交。
    user = sample_user
    user.is_active = False
    session.add(user)
    session.commit()

    # 2. 为该用户创建一个有效的 token
    token = create_access_token(data={"sub": str(user.id)})

    # 3. 覆盖 get_db 依赖
    app.dependency_overrides[deps.get_db] = lambda: session
    # 4. 发送请求到 /test-active-user
    response = client.get("/test-active-user", headers={"Authorization": f"Bearer {token}"})

    # 5. 断言 status_code 是否为 400，并且 detail 信息为 "Inactive user"
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 6. 清理依赖覆盖
    app.dependency_overrides = {}


def test_get_current_superuser_with_normal_user(session: Session, sample_user: User) -> None:
    """
    测试: 验证一个普通用户（非管理员）在访问需要超级用户权限的端点时，会被正确地拒绝
    预期: 抛出 403 HTTPException
    """
    # 1. 使用 sample_user fixture，它默认就是一个普通用户。
    # 2. 为这个普通用户创建一个有效的 Token。
    token = create_access_token(data={"sub": str(sample_user.id)})

    # 3. 覆盖 get_db 依赖。
    app.dependency_overrides[deps.get_db] = lambda: session

    # 4. 向 /test-superuser 端点发送请求。
    response = client.get("/test-superuser", headers={"Authorization": f"Bearer {token}"})

    # 5. 断言：
    #  * response.status_code 应该是 403 (Forbidden)。
    #  * response.json()["detail"] 应该是 "The user doesn't have enough privileges"。
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "The user doesn't have enough privileges" in response.json()["detail"]

    #    6. 清理依赖覆盖。
    app.dependency_overrides = {}



def test_get_current_superuser_with_admin_user(session: Session, sample_user: User) -> None:
    """
    测试: 验证一个管理员用户可以成功访问需要超级用户权限的端点
    预期: 成功返回对应的用户
    """
    # 1. 需要一个管理员用户。你可以直接修改 sample_user 的 role 属性，或者创建一个新的管理员用户。
    user = sample_user
    user.promote_to_admin()
    session.add(user)
    session.commit()

    assert user.is_admin is True

    # 2. 为这个管理员用户创建一个有效的 Token。
    token = create_access_token(data={"sub": str(user.id)})

    # 3. 覆盖 get_db 依赖。
    app.dependency_overrides[deps.get_db] = lambda: session

    # 4. 向 /test-superuser 端点发送请求。
    response = client.get(url="/test-superuser", headers={"Authorization": f"Bearer {token}"})
    # 5. 断言：
    #     * response.status_code 应该是 200 (OK)。
    #     * 返回的 JSON 数据中的 "role" 字段应该是 "admin"。
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

    # 6. 清理依赖覆盖。
    app.dependency_overrides = {}
