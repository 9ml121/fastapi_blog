"""
User CRUD - 用户数据操作层

包含所有与 User 模型相关的数据库操作（创建、读取、更新、删除）。

设计原则：
1. 所有查询函数都过滤 deleted_at（软删除用户不应被查询到）
2. 使用关键字参数（*, param）提高可读性
3. 更新操作使用部分更新（exclude_unset=True）
4. 删除操作使用软删除（设置 deleted_at）
"""

import random
import string
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidVerificationCodeError,
    ResourceNotFoundError,
    UsernameAlreadyExistsError,
)
from app.core.security import hash_password, verify_password
from app.db.redis_client import verify_code
from app.models.user import User
from app.schemas.user import UserCreate, UserProfileUpdate, UserUpdate


#  ===================== 辅助函数 ===================
def _generate_unique_username(db: Session, email: str) -> str:
    """基于邮箱生成唯一的用户名"""
    # 1. 提取邮箱前缀 (split 是分割字符串，[0] 取第一部分)
    # email: "zhang.san@example.com" -> prefix: "zhang.san"
    prefix = email.split("@")[0]

    # 2. 清理非法字符 (可选，但推荐)
    # 将 "." 替换为 "_"，确保符合 URL 规范
    # "zhang.san" -> "zhang_san"
    base_username = prefix.replace(".", "_")

    # 3. 第一次尝试：直接用前缀
    candidate = base_username

    if not get_user_by_username(db, username=candidate):
        return candidate

    # 4. 如果冲突，开始循环尝试追加随机后缀
    while True:
        # 生成 4 位随机字符 (数字+小写字母)，如 "8a2b"
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=4)
        )

        # 拼接：zhang_san_8a2b
        candidate = f"{base_username}_{random_suffix}"

        # 再次查库
        if not get_user_by_username(db, username=candidate):
            return candidate


#  ===================== 用户查询 ===================
def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """通过用户 ID 查询用户（主键查询）"""
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    """通过邮箱地址查询用户"""
    return (
        db.query(User)
        .filter(
            User.email == email,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    """通过用户名查询用户"""
    return (
        db.query(User)
        .filter(
            User.username == username,
            User.deleted_at.is_(None),  # 软删除过滤
        )
        .first()
    )


#  =================================== 用户创建 ===================================
def create_user(db: Session, *, user_in: UserCreate) -> User:
    """创建新用户

    description: 包含验证码验证、邮箱唯一性检查、用户名生成、密码哈希逻辑
    """
    # 1. 验证码校验
    if not verify_code(email=user_in.email, code=user_in.verification_code):
        raise InvalidVerificationCodeError()

    # 2.检查邮箱唯一性
    if get_user_by_email(db, email=user_in.email):
        raise EmailAlreadyExistsError(email=user_in.email)

    # 3. 生成唯一的用户名
    username = _generate_unique_username(db, email=user_in.email)

    # === 生成默认头像 URL ===
    # 使用 ui-avatars，背景随机，颜色白色：https://ui-avatars.com/
    # 也可以换成 DiceBear: https://dicebear.com
    # avatar_url = f"https://ui-avatars.com/api/?name={username}&background=random&color=fff"
    avatar_url = f"https://api.dicebear.com/9.x/adventurer/svg?seed={username}"

    # 4. 处理密码与数据转换(排除 schema 中有但 model 中没有的字段)
    user_data = user_in.model_dump(exclude={"password", "verification_code"})
    hashed_password = hash_password(user_in.password)

    # 5. 创建模型实例并存库
    db_user = User(
        **user_data,
        username=username,
        avatar=avatar_url,
        password_hash=hashed_password,
        is_active=True,
        is_verified=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


#  =================================== 用户登录验证 ===================================
def authenticate_user(db: Session, *, identifier: str, password: str) -> User | None:
    """用户登录验证（支持邮箱或用户名 + 密码）

    设计要点 - 安全考量：
    1. 支持邮箱或用户名登录：
       - 先尝试邮箱查询
       - 如果没找到，再尝试用户名查询
    2. 防止时序攻击（Timing Attack）：
       - 即使用户不存在，也执行假的密码验证（dummy）
       - 确保成功/失败的响应时间相似
    3. 统一错误信息：
       - 不泄露"用户不存在"或"密码错误"的具体原因
       - API 层应返回统一的"用户名或密码错误"
    4. 验证用户状态：
       - 已删除用户（deleted_at != None）无法登录
       - 可选：检查 is_active（管理员禁用）

    Args:
        db: 数据库会话对象
        identifier: 用户邮箱或用户名
        password: 明文密码

    Returns:
        验证成功返回 User 对象，失败返回 None
    """
    # 1. 查询用户（先尝试邮箱，再尝试用户名）
    user = get_user_by_email(db, email=identifier)
    if not user:
        user = get_user_by_username(db, username=identifier)

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
    if not user.is_active:
        return None

    # 5. 验证成功，返回用户对象
    return user


#  =================================== 用户更新 ===================================
def update_user(db: Session, *, user_id: UUID, user_in: UserUpdate) -> User | None:
    """更新用户信息（管理员更新,包含用户管理，密码重置，账户激活/停用）

    设计要点：
    ✅ 管理员权限：可以更新任意用户
    ✅ 完整权限：可以更新所有字段包括 is_active
    ✅ 包含密码：可以重置用户密码
    ✅ 用户名更新：可以修改用户名

    Args:
        db: 数据库会话对象
        user_id: 要更新的用户 ID
        user_in: UserUpdate schema更新的字段

    Returns:
        更新后的 User 模型对象或 None（用户不存在）
    """
    # 1. 查询用户（排除软删除）
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise ResourceNotFoundError(resource="用户")

    # 2. 如果更新邮箱，检查新邮箱是否已被占用（排除自己）
    if user_in.email and user_in.email != user.email:
        existing_user = get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user.id:
            raise EmailAlreadyExistsError(email=user_in.email)

    # 3. 如果更新用户名，检查新用户名是否已被占用（排除自己）
    if user_in.username and user_in.username != user.username:
        existing_user = get_user_by_username(db, username=user_in.username)
        if existing_user and existing_user.id != user.id:
            raise UsernameAlreadyExistsError(username=user_in.username)

    # 4. 提取实际提供的字段（exclude_unset=True）
    update_data = user_in.model_dump(exclude_unset=True)

    # 5. 处理密码更新（如果提供了密码）
    if "password" in update_data:
        hashed_password = hash_password(update_data.pop("password"))
        update_data["password_hash"] = hashed_password

    # 6. 逐个更新字段
    for field, value in update_data.items():
        setattr(user, field, value)

    # 7. 提交更新
    db.commit()
    db.refresh(user)

    return user


def update_profile(
    db: Session, *, user: User, profile_update: UserProfileUpdate
) -> User:
    """用户自主更新个人资料（个人资料管理、邮箱更换等）

    设计要点：
    1. 只更新用户自己的资料，不允许修改他人资料
    2. 邮箱去重检查（排除用户自己的邮箱）
    3. 只更新实际提供的字段（exclude_unset=True）
    4. 不包含权限相关字段（is_active，role）
    5. 不包含密码更新（使用单独端点）
    6. 不包含用户名更新

    Args:
        db: 数据库会话对象
        user: 当前用户对象（已通过认证）
        profile_update: 用户资料更新数据

    Returns:
        更新后的用户对象

    Raises:
        ValueError: 当邮箱已被其他用户使用时
    """
    # 1. 如果更新邮箱，检查新邮箱是否已被占用（排除自己）
    if profile_update.email and profile_update.email != user.email:
        existing_user = get_user_by_email(db, email=profile_update.email)
        if existing_user and existing_user.id != user.id:
            raise EmailAlreadyExistsError(email=profile_update.email)

    # 2. 只提取实际提供的字段（exclude_unset=True 实现 PATCH 语义）
    update_data = profile_update.model_dump(exclude_unset=True)

    # 3. 逐个更新字段
    for field, value in update_data.items():
        setattr(user, field, value)

    # 4. 提交更新（updated_at 由数据库自动更新）
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    """更新用户密码(用于修改和重置密码 2 个场景)

    更新：此函数只负责修改密码，不做权限验证。权限验证（验证码/旧密码）由 API 层负责。

    Args:
        db: 数据库会话对象
        user: 当前用户对象（已通过认证）
        new_password: 新密码

    Returns:
        更新后的用户对象
    """
    user.password_hash = hash_password(new_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


#  =================================== 用户删除 ===================================


def delete_user(db: Session, user_id: UUID) -> User | None:
    """软删除用户（设置 deleted_at 时间戳）

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
        raise ResourceNotFoundError(resource="用户")

    # 2. 设置软删除时间戳
    user.deleted_at = datetime.now(UTC)

    # 3. 提交更新
    db.commit()
    db.refresh(user)

    return user
