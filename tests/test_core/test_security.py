"""
Test Security Module - 安全模块测试

测试目标：

1. 密码安全（bcrypt）：
- 验证密码哈希生成是否符合 bcrypt 格式
- 验证密码验证逻辑的正确性
- 验证 salt 唯一性（相同密码生成不同哈希）
- 覆盖边界条件（空字符串、特殊字符）

2. JWT Token 认证：
- 验证 token 生成功能（包含用户信息）
- 验证 token 解码和验证功能（正常 token）
- 验证 token 过期处理（过期 token）
- 验证无效 token 处理（篡改、格式错误）
- 验证输入数据不被修改（data.copy() 机制）
"""

import re
import time
from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

# 验证哈希格式：$2b$12$[22字符salt][31字符hash]
# bcrypt 格式：$<version>$<rounds>$<salt><hash>
BCRYPT_PATTERN = re.compile(r"^\$2b\$\d{2}\$[A-Za-z0-9./]{53}$")


def test_hash_password_returns_valid_hash() -> None:
    """测试：hash_password() 应该返回有效的 bcrypt 哈希值"""
    password = "TestPassword123"
    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$")  # bcrypt 版本标识

    # 使用正则验证完整格式
    assert BCRYPT_PATTERN.match(hashed), f"哈希格式不正确: {hashed}"


def test_verify_password_correct() -> None:
    """测试：verify_password() 应该能验证正确的密码"""
    password = "MySecret123"
    hashed = hash_password(password)

    # 使用相同的密码应该验证成功
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect() -> None:
    """测试：verify_password() 应该拒绝错误的密码"""
    password = "MySecret123"
    wrong_password = "WrongPassword"
    hashed = hash_password(password)

    # 使用错误的密码应该验证失败
    assert verify_password(wrong_password, hashed) is False


# 实现 Salt 唯一性测试
def test_same_password_different_hashes() -> None:
    """测试：相同密码应该生成不同的哈希值（salt 唯一性）"""
    # 1. 使用相同密码调用 hash_password() 两次
    password = "MySecret123"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    # 2. 验证两次生成的哈希值不同（因为 salt 随机）
    assert hashed1 != hashed2

    # 3. 但两个哈希都应该能验证原始密码（用 verify_password）
    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True


# 实现边界条件测试
def test_hash_password_empty_string() -> None:
    """测试：空字符串密码应该也能正常哈希和验证"""
    password = ""
    hashed = hash_password(password)

    assert BCRYPT_PATTERN.match(hashed), f"哈希格式不正确: {hashed}"
    assert verify_password(password, hashed) is True


def test_hash_password_special_characters() -> None:
    """测试：包含特殊字符的密码应该正常工作"""

    # 1. 使用包含特殊字符的密码
    password = "P@ssw0rd!#$%^&*()"
    hashed = hash_password(password)

    # 2. 验证能正常哈希
    assert BCRYPT_PATTERN.match(hashed), f"哈希格式不正确: {hashed}"
    # 3. 验证能正确验证
    assert verify_password(password, hashed) is True


# ==========================================
# JWT Token 测试
# ==========================================


def test_create_access_token() -> None:
    """测试：create_access_token() 应该生成有效的 JWT token"""
    # 准备测试数据（通常包含用户 ID）
    data = {"sub": "user123"}

    # 生成 token
    token = create_access_token(data)

    # 验证 token 是字符串
    assert isinstance(token, str)

    # JWT 格式：header.payload.signature（三部分用 . 分隔）
    parts = token.split(".")
    assert len(parts) == 3, "JWT token 应该有 3 部分（header.payload.signature）"


def test_create_access_token_with_custom_expiry() -> None:
    """测试：create_access_token() 应该支持自定义过期时间"""
    data = {"sub": "user123"}
    custom_delta = timedelta(minutes=15)

    # 生成自定义过期时间的 token
    token = create_access_token(data, expires_delta=custom_delta)

    # 验证能解码（说明 token 有效）
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"


def test_decode_access_token_valid() -> None:
    """测试：decode_access_token() 应该能解码有效的 token"""
    # 1. 创建 token
    data = {"sub": "user123", "email": "test@example.com"}
    token = create_access_token(data)

    # 2. 解码 token
    payload = decode_access_token(token)

    # 3. 验证解码结果
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload  # 应该包含过期时间


def test_decode_access_token_expired() -> None:
    """测试：decode_access_token() 应该拒绝过期的 token"""
    # 1. 创建一个立即过期的 token（过期时间设置为 1 秒）
    data = {"sub": "user123"}
    token = create_access_token(data, expires_delta=timedelta(seconds=1))

    # 2. 等待 token 过期
    time.sleep(2)  # 等待 2 秒确保过期

    # 3. 尝试解码过期的 token
    payload = decode_access_token(token)

    # 4. 应该返回 None（token 已过期）
    assert payload is None


def test_decode_access_token_invalid_format() -> None:
    """测试：decode_access_token() 应该拒绝格式错误的 token"""
    # 测试各种无效的 token 格式
    invalid_tokens = [
        "not.a.jwt",  # 格式正确但内容无效
        "invalid_token",  # 完全无效的字符串
        "a.b",  # 只有两部分
        "",  # 空字符串
    ]

    for invalid_token in invalid_tokens:
        payload = decode_access_token(invalid_token)
        assert payload is None, f"应该拒绝无效 token: {invalid_token}"


def test_decode_access_token_tampered() -> None:
    """测试：decode_access_token() 应该拒绝被篡改的 token"""
    # 1. 创建一个有效的 token
    data = {"sub": "user123"}
    token = create_access_token(data)

    # 2. 篡改 token（修改 payload 部分）
    parts = token.split(".")
    # 修改中间部分（payload）的最后一个字符
    tampered_payload = parts[1][:-1] + ("a" if parts[1][-1] != "a" else "b")
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    # 3. 尝试解码被篡改的 token
    payload = decode_access_token(tampered_token)

    # 4. 应该返回 None（签名验证失败）
    assert payload is None


def test_create_token_does_not_mutate_input() -> None:
    """测试：create_access_token() 不应该修改输入的 data 字典"""
    # 1. 准备原始数据
    original_data = {"sub": "user123", "email": "test@example.com"}
    data_copy = original_data.copy()

    # 2. 创建 token
    create_access_token(original_data)

    # 3. 验证原始数据未被修改（没有添加 exp 字段）
    assert original_data == data_copy
    assert "exp" not in original_data
