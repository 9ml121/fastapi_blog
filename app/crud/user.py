"""
User CRUD - 用户数据操作层

包含所有与 User 模型相关的数据库操作（创建、读取、更新、删除）。

设计原则：
1. 所有查询函数都过滤 deleted_at（软删除用户不应被查询到）
2. 使用关键字参数（*, param）提高可读性
3. 更新操作使用部分更新（exclude_unset=True）
4. 删除操作使用软删除（设置 deleted_at）
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, *, user_id: UUID) -> User | None:
    """
    通过用户 ID 查询用户（主键查询）

    设计要点：
    - 主键查询性能最优（数据库索引）
    - 常用于从 JWT token 解析出 user_id 后查询用户
    - 过滤软删除用户（deleted_at.is_(None)）

    Args:
        db: 数据库会话对象
        user_id: 用户 UUID

    Returns:
        User 模型对象或 None
    """
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


def get_user_by_email(db: Session, *, email: str) -> User | None:
    """
    通过邮箱地址查询用户

    设计要点：
    - 邮箱有唯一约束和索引，查询性能好
    - 用于登录（邮箱登录）、注册时检查重复
    - 过滤软删除用户

    Args:
        db: 数据库会话对象
        email: 要查询的邮箱地址

    Returns:
        User 模型对象或 None
    """
    return (
        db.query(User)
        .filter(
            User.email == email,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


def get_user_by_username(db: Session, *, username: str) -> User | None:
    """
    通过用户名查询用户

    设计要点：
    - 用户名有唯一约束和索引
    - 用于登录（用户名登录）、注册时检查重复
    - 过滤软删除用户

    Args:
        db: 数据库会话对象
        username: 用户名

    Returns:
        User 模型对象或 None
    """
    return (
        db.query(User)
        .filter(
            User.username == username,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


def create_user(db: Session, *, user_in: UserCreate) -> User:
    """
    创建新用户

    Args:
        db: 数据库会话对象
        user_in: Pydantic UserCreate schema 对象，包含新用户信息

    Returns:
        新创建的 User 模型对象
    """
    # 1. 从输入的 schema 中提取不含密码的数据
    user_data = user_in.model_dump(exclude={"password"})

    # 2. 对密码进行哈希处理
    hashed_password = hash_password(user_in.password)

    # 3. 创建 SQLAlchemy User 模型实例
    db_user = User(**user_data, password_hash=hashed_password)

    # 4. 将实例添加到数据库会话、提交事务、刷新实例
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def update_user(db: Session, *, user_id: UUID, user_in: UserUpdate) -> User | None:
    """
    更新用户信息（部分更新）

    设计要点：
    1. 使用 model_dump(exclude_unset=True) 只更新提供的字段
    2. 密码更新需要单独处理（哈希）
    3. 某些字段（如 is_superuser）不应允许通过此接口更新
    4. updated_at 由数据库自动更新（onupdate=func.now()）

    Args:
        db: 数据库会话对象
        user_id: 要更新的用户 ID
        user_in: Pydantic UserUpdate schema，包含要更新的字段

    Returns:
        更新后的 User 模型对象或 None（用户不存在）
    """
    # 1. 查询用户（排除软删除）
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None

    # 2. 只提取实际提供的字段（exclude_unset=True）
    update_data = user_in.model_dump(exclude_unset=True)

    # 3. 处理密码更新（如果提供了密码）
    if "password" in update_data:
        hashed_password = hash_password(update_data.pop("password"))
        update_data["password_hash"] = hashed_password

    # 4. 逐个更新字段
    for field, value in update_data.items():
        setattr(user, field, value)

    # 5. 提交更新
    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, *, user_id: UUID) -> User | None:
    """
    软删除用户（设置 deleted_at 时间戳）

    设计要点：
    1. 软删除：设置 deleted_at = 当前时间，数据不会真正删除
    2. 优势：可以恢复账号（30天内）、保留数据完整性、审计追溯
    3. 与 is_active 区分：
       - is_active=False → 管理员临时禁用
       - deleted_at != None → 用户主动删除账号

    Args:
        db: 数据库会话对象
        user_id: 要删除的用户 ID

    Returns:
        被删除的 User 模型对象或 None（用户不存在）
    """
    # 1. 查询用户（排除已删除）
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None

    # 2. 设置软删除时间戳
    user.deleted_at = datetime.now()

    # 3. 提交更新
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    """
    用户登录验证（邮箱 + 密码）

    设计要点 - 安全考量：
    1. 防止时序攻击（Timing Attack）：
       - 即使用户不存在，也执行假的密码验证（dummy）
       - 确保成功/失败的响应时间相似
    2. 统一错误信息：
       - 不泄露"用户不存在"或"密码错误"的具体原因
       - API 层应返回统一的"用户名或密码错误"
    3. 验证用户状态：
       - 已删除用户（deleted_at != None）无法登录
       - 可选：检查 is_active（管理员禁用）

    Args:
        db: 数据库会话对象
        email: 用户邮箱
        password: 明文密码

    Returns:
        验证成功返回 User 对象，失败返回 None
    """
    # 1. 查询用户（排除软删除）
    user = get_user_by_email(db, email=email)

    # 2. 防止时序攻击：即使用户不存在，也执行假的密码验证
    if not user:
        # 使用一个真实的 bcrypt 哈希作为 dummy（但永远不会匹配）
        # 这样既能保持验证时间一致，又不会抛出 "Invalid salt" 异常
        # 注意：这个哈希是 "dummy_password" 的哈希值，但输入不会是这个
        dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.TjXqzi"
        verify_password(password, dummy_hash)
        return None

    # 3. 验证密码
    if not verify_password(password, user.password_hash):
        return None

    # 4. 可选：检查用户是否被禁用（根据业务需求）
    # if not user.is_active:
    #     return None

    # 5. 验证成功，返回用户对象
    return user
