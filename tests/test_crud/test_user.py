"""
Test User CRUD - 用户数据操作层测试

测试目标：
- 验证 `create_user` 函数能否正确创建用户并哈希密码
- 验证所有查询函数（by_id、by_email、by_username）
- 验证 `update_user` 部分更新和密码更新
- 验证 `delete_user` 软删除功能
- 验证 `authenticate_user` 认证功能和安全性
- 覆盖唯一性约束等边界条件
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import crud
from app.core.exceptions import (
    EmailAlreadyExistsError,
    ResourceNotFoundError,
    UsernameAlreadyExistsError,
)
from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def test_create_user(session: Session) -> None:
    """测试：成功创建一个新用户"""
    # 准备测试数据
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    user_in = UserCreate(email=email, password=password, username=username)

    # 执行创建操作
    user: User = crud.user.create_user(db=session, user_in=user_in)

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
    user: User | None = crud.user.get_user_by_email(db=session, email=email)

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

    # 断言这会抛出邮箱重复错误
    with pytest.raises(EmailAlreadyExistsError):
        crud.user.create_user(db=session, user_in=user_in_2)


def test_create_user_with_duplicate_username(session: Session) -> None:
    """测试：使用重复的用户名创建用户应该失败"""
    username = "duplicateuser"
    user_in_1 = UserCreate(
        email="user1@example.com", password="TestPassword123", username=username
    )
    crud.user.create_user(db=session, user_in=user_in_1)

    user_in_2 = UserCreate(
        email="user2@example.com", password="TestPassword123", username=username
    )

    with pytest.raises(UsernameAlreadyExistsError):
        crud.user.create_user(db=session, user_in=user_in_2)


# ============ 查询测试：get_user_by_id ============


def test_get_user_by_id(session: Session) -> None:
    """测试：通过用户 ID 查询用户"""
    user_in = UserCreate(
        email="test@example.com", password="TestPassword123", username="testuser"
    )
    created_user = crud.user.create_user(db=session, user_in=user_in)

    # 通过 ID 查询
    user = crud.user.get_user_by_id(db=session, user_id=created_user.id)

    assert user is not None
    assert user.id == created_user.id
    assert user.email == created_user.email


def test_get_user_by_non_existent_id(session: Session) -> None:
    """测试：使用不存在的 ID 查询应该返回 None"""
    user = crud.user.get_user_by_id(db=session, user_id=uuid4())
    assert user is None


# ============ 查询测试：get_user_by_username ============


def test_get_user_by_username(session: Session) -> None:
    """测试：通过用户名查询用户"""
    username = "testuser"
    user_in = UserCreate(
        email="test@example.com", password="TestPassword123", username=username
    )
    crud.user.create_user(db=session, user_in=user_in)

    user = crud.user.get_user_by_username(db=session, username=username)

    assert user is not None
    assert user.username == username


def test_get_user_by_non_existent_username(session: Session) -> None:
    """测试：使用不存在的用户名查询应该返回 None"""
    user = crud.user.get_user_by_username(db=session, username="nonexistent")
    assert user is None


# ============ 更新测试：update_user ============


def test_update_user_partial(session: Session) -> None:
    """测试：部分更新用户信息（只更新提供的字段）"""
    # 创建用户
    user_in = UserCreate(
        email="test@example.com", password="TestPassword123", username="testuser"
    )
    user = crud.user.create_user(db=session, user_in=user_in)
    original_email = user.email
    original_password_hash = user.password_hash

    # 只更新 nickname
    user_update = UserUpdate(nickname="新昵称")
    updated_user = crud.user.update_user(
        db=session, user_id=user.id, user_in=user_update
    )

    assert updated_user is not None
    assert updated_user.nickname == "新昵称"
    assert updated_user.email == original_email  # 邮箱未变
    assert updated_user.password_hash == original_password_hash  # 密码未变


def test_update_user_password(session: Session) -> None:
    """测试：更新用户密码（需要哈希处理）"""
    # 创建用户
    old_password = "OldPassword123"
    user_in = UserCreate(
        email="test@example.com", password=old_password, username="testuser"
    )
    user: User = crud.user.create_user(db=session, user_in=user_in)
    old_password_hash = user.password_hash
    print(repr(user))

    # 更新密码
    new_password = "NewPassword456"
    updated_user = crud.user.update_password(
        db=session, user=user, old_password=old_password, new_password=new_password
    )

    assert updated_user is not None
    # 密码哈希已改变
    assert updated_user.password_hash != old_password_hash
    # 新密码验证通过
    assert verify_password(new_password, updated_user.password_hash)
    # 旧密码验证失败
    assert not verify_password(old_password, updated_user.password_hash)


def test_update_non_existent_user(session: Session) -> None:
    """测试：更新不存在的用户应该抛出 ResourceNotFoundError"""
    user_update = UserUpdate(nickname="新昵称")
    with pytest.raises(ResourceNotFoundError):
        crud.user.update_user(db=session, user_id=uuid4(), user_in=user_update)


# ============ 删除测试：delete_user（软删除）============


def test_delete_user(session: Session) -> None:
    """测试：软删除用户（设置 deleted_at）"""
    # 创建用户
    user_in = UserCreate(
        email="test@example.com", password="TestPassword123", username="testuser"
    )
    user: User = crud.user.create_user(db=session, user_in=user_in)
    user_id = user.id

    # 软删除用户
    deleted_user: User | None = crud.user.delete_user(db=session, user_id=user_id)

    assert deleted_user is not None
    assert deleted_user.deleted_at is not None  # 软删除时间已设置


def test_delete_non_existent_user(session: Session) -> None:
    """测试：删除不存在的用户应该抛出 ResourceNotFoundError"""
    with pytest.raises(ResourceNotFoundError):
        crud.user.delete_user(db=session, user_id=uuid4())


def test_soft_deleted_user_not_queryable(session: Session) -> None:
    """测试：软删除的用户无法通过查询函数获取"""
    # 创建并删除用户
    user_in = UserCreate(
        email="test@example.com", password="TestPassword123", username="testuser"
    )
    user = crud.user.create_user(db=session, user_in=user_in)
    user_id = user.id
    email = user.email
    username = user.username

    crud.user.delete_user(db=session, user_id=user_id)

    # 尝试查询已删除的用户（应该返回 None）
    assert crud.user.get_user_by_id(db=session, user_id=user_id) is None
    assert crud.user.get_user_by_email(db=session, email=email) is None
    assert crud.user.get_user_by_username(db=session, username=username) is None


# ============ 认证测试：authenticate_user ============


def test_authenticate_user_success(session: Session) -> None:
    """测试：使用正确的邮箱和密码认证成功"""
    email = "test@example.com"
    password = "TestPassword123"
    user_in = UserCreate(email=email, password=password, username="testuser")
    crud.user.create_user(db=session, user_in=user_in)

    # 认证成功
    user: User | None = crud.user.authenticate_user(
        db=session, identifier=email, password=password
    )

    assert user is not None
    assert user.email == email


def test_authenticate_user_wrong_password(session: Session) -> None:
    """测试：错误的密码应该认证失败"""
    email = "test@example.com"
    password = "CorrectPassword123"
    user_in = UserCreate(email=email, password=password, username="testuser")
    crud.user.create_user(db=session, user_in=user_in)

    # 错误的密码
    user = crud.user.authenticate_user(
        db=session, identifier=email, password="WrongPassword"
    )

    assert user is None


def test_authenticate_non_existent_user(session: Session) -> None:
    """测试：不存在的用户应该认证失败（防止时序攻击）"""
    user = crud.user.authenticate_user(
        db=session, identifier="nonexistent@example.com", password="AnyPassword"
    )
    assert user is None


def test_authenticate_soft_deleted_user(session: Session) -> None:
    """测试：软删除的用户无法登录"""
    email = "test@example.com"
    password = "TestPassword123"
    user_in = UserCreate(email=email, password=password, username="testuser")
    user = crud.user.create_user(db=session, user_in=user_in)

    # 软删除用户
    crud.user.delete_user(db=session, user_id=user.id)

    # 尝试认证（应该失败）
    result = crud.user.authenticate_user(
        db=session, identifier=email, password=password
    )
    assert result is None
