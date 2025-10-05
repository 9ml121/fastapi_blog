"""
Test User CRUD - 用户数据操作层测试

测试目标：
- 验证 `create_user` 函数能否正确创建用户并哈希密码
- 验证 `get_user_by_email` 函数能否正确查询用户
- 覆盖唯一性约束等边界条件
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserCreate


def test_create_user(session: Session) -> None:
    """测试：成功创建一个新用户"""
    # 准备测试数据
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    user_in = UserCreate(email=email, password=password, username=username)

    # 执行创建操作
    user = crud.user.create_user(db=session, user_in=user_in)

    # 断言返回的对象符合预期
    assert user.email == email
    assert user.username == username
    assert hasattr(user, "password_hash")

    # 验证密码哈希是否正确
    assert verify_password(password, user.password_hash)


def test_get_user_by_email(session: Session) -> None:
    """测试：通过邮箱获取用户"""
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    user_in = UserCreate(email=email, password=password, username=username)
    crud.user.create_user(db=session, user_in=user_in)

    # 执行查询操作
    user = crud.user.get_user_by_email(db=session, email=email)

    # 断言找到了正确的用户
    assert user
    assert user.email == email
    assert user.username == username


def test_get_user_by_non_existent_email(session: Session) -> None:
    """测试：使用不存在的邮箱查询应该返回 None"""
    user = crud.user.get_user_by_email(db=session, email="nonexistent@example.com")
    assert user is None


def test_create_user_with_duplicate_email(session: Session) -> None:
    """测试：使用重复的邮箱创建用户应该失败"""
    # 先创建一个用户
    email = "duplicate@example.com"
    password = "TestPassword123"
    user_in_1 = UserCreate(email=email, password=password, username="user1")
    crud.user.create_user(db=session, user_in=user_in_1)

    # 尝试使用相同的邮箱创建第二个用户
    user_in_2 = UserCreate(email=email, password=password, username="user2")

    # 断言这会因为唯一性约束而抛出 IntegrityError
    with pytest.raises(IntegrityError):
        crud.user.create_user(db=session, user_in=user_in_2)
