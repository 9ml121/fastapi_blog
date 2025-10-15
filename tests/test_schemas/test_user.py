"""
Test User Schemas - Pydantic 数据验证测试

测试目标：
- 验证 UserCreate schema 的数据验证逻辑是否按预期工作
- 覆盖有效数据、无效数据和边界条件
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate

# 定义一个基础的、完全有效的数据字典，用于测试
VALID_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "ValidPass123",
}


def test_user_create_valid_data():
    """测试：使用完全有效的数据创建 UserCreate 实例应该成功"""
    # 使用有效数据创建实例
    user = UserCreate(**VALID_USER_DATA)
    # 验证字段是否被正确赋值
    assert user.username == VALID_USER_DATA["username"]
    assert user.email == VALID_USER_DATA["email"]
    assert user.password == VALID_USER_DATA["password"]


@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [
        pytest.param(
            "short", "String should have at least 8 characters", id="password_too_short"
        ),
        pytest.param(
            "onlyletters", "密码必须包含至少一个数字", id="password_no_digits"
        ),
        pytest.param("12345678", "密码必须包含至少一个字母", id="password_no_letters"),
    ],
)
def test_user_create_invalid_password(invalid_password: str, expected_error_msg: str):
    """测试：使用无效的密码创建 UserCreate 实例应该失败"""
    data = VALID_USER_DATA.copy()
    data["password"] = invalid_password

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**data)

    assert any(expected_error_msg in str(e) for e in excinfo.value.errors())


@pytest.mark.parametrize(
    ("invalid_username", "expected_error_msg"),
    [
        pytest.param(
            "a", "String should have at least 3 characters", id="username_too_short"
        ),
        pytest.param(
            "a" * 51, "String should have at most 50 characters", id="username_too_long"
        ),
        pytest.param(
            "user@!", "String should match pattern", id="username_invalid_chars"
        ),
    ],
)
def test_user_create_invalid_username(invalid_username: str, expected_error_msg: str):
    """测试：使用无效的用户名创建 UserCreate 实例应该失败"""
    data = VALID_USER_DATA.copy()
    data["username"] = invalid_username

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**data)

    assert any(expected_error_msg in e["msg"] for e in excinfo.value.errors())
