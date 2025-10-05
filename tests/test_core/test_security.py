"""
Test Password Security - 密码安全功能测试

测试目标：
- 验证密码哈希生成是否符合 bcrypt 格式
- 验证密码验证逻辑的正确性
- 验证 salt 唯一性（相同密码生成不同哈希）
- 覆盖边界条件（空字符串、特殊字符）
"""

import re

from app.core.security import hash_password, verify_password

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
