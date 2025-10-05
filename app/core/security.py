"""
密码安全工具 - Password Security Utilities

提供密码哈希和验证功能，使用 bcrypt 算法确保密码安全存储。

核心概念：
1. 哈希（Hash）：单向加密，不可逆
2. 盐值（Salt）：随机字符串，防彩虹表攻击（bcrypt 自动处理）
3. 慢速哈希：计算成本高，防暴力破解

技术选择：
- 算法：bcrypt（行业标准）
- 库：bcrypt（直接使用，简单可靠）
- 成本参数：rounds=12（2^12=4096次迭代，约0.1秒）
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    将明文密码转换为 bcrypt 哈希值

    工作原理：
    1. 自动生成随机 salt（bcrypt 内部处理）
    2. 将密码 + salt 进行 bcrypt 哈希（rounds=12，默认4096次迭代）
    3. 返回包含版本、rounds、salt、哈希的完整字符串

    Args:
        password: 明文密码

    Returns:
        bcrypt 哈希字符串，格式：$2b$12$[salt][hash]
        示例：$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy

    安全性：
    - 相同密码，每次哈希结果不同（salt 随机）
    - 哈希不可逆，无法还原原始密码
    - 计算成本高（~0.1秒），抵抗暴力破解

    示例：
        >>> hashed = hash_password("MySecret123")
        >>> print(hashed)
        $2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
    """
    # bcrypt 需要 bytes 输入
    password_bytes = password.encode("utf-8")

    # 生成 salt（rounds=12，即2^12=4096次迭代）
    salt = bcrypt.gensalt(rounds=12)

    # 计算哈希值
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)

    # 返回字符串格式
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希值匹配

    工作原理：
    1. 从 hashed_password 中提取 salt 和 rounds
    2. 使用相同的 salt 和 rounds 对 plain_password 进行哈希
    3. 对比新哈希值与 hashed_password 是否一致

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的 bcrypt 哈希值

    Returns:
        True: 密码匹配
        False: 密码不匹配

    注意：
    - 不解密哈希值（不可能）
    - 重新计算哈希，然后对比（确定性）
    - 执行时间约 0.1秒（防止时序攻击，bcrypt 内部处理）

    示例：
        >>> hashed = hash_password("MySecret123")
        >>> verify_password("MySecret123", hashed)  # 正确密码
        True
        >>> verify_password("WrongPass", hashed)    # 错误密码
        False
    """
    # 转换为 bytes
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    # bcrypt.checkpw 会自动从 hashed_bytes 中提取 salt 并重新计算
    return bcrypt.checkpw(password_bytes, hashed_bytes)
