"""
安全工具模块 - Security Utilities

提供两大核心功能：
1. 密码安全：bcrypt 哈希和验证
2. JWT 认证：token 生成和验证

密码安全核心概念：
1. 哈希（Hash）：单向加密，不可逆
2. 盐值（Salt）：随机字符串，防彩虹表攻击（bcrypt 自动处理）
3. 慢速哈希：计算成本高，防暴力破解

JWT 认证核心概念：
1. 无状态认证：token 自包含所有信息
2. 签名验证：防篡改（HMAC-SHA256）
3. 过期控制：自动失效机制

技术选择：
- 密码哈希：bcrypt（rounds=12，约0.1秒）
- JWT 库：python-jose（FastAPI 官方推荐）
- 签名算法：HS256（对称加密，适合单体应用）
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


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


# ==========================================
# JWT Token 认证工具
# ==========================================


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT access token

    工作原理：
    1. 复制输入数据（避免修改原数据）
    2. 添加过期时间（exp claim）
    3. 使用 SECRET_KEY 和 HS256 算法签名
    4. 返回 JWT 字符串

    Args:
        data: 要编码到 token 中的数据（通常包含 sub: user_id）
        expires_delta: token 有效期，如果不提供则使用配置的默认值

    Returns:
        JWT token 字符串，格式：header.payload.signature
        示例：eyJhbGci...（Base64 编码）

    Token 结构：
        Header: {"alg": "HS256", "typ": "JWT"}
        Payload: {"sub": "user_id", "exp": 1234567890, ...}
        Signature: HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)

    安全性：
    - 签名防篡改：任何修改 payload 都会导致签名验证失败
    - 自动过期：exp 字段由 jose 库自动检查
    - 无需存储：token 自包含所有信息（无状态）

    示例：
        >>> from datetime import timedelta
        >>> token = create_access_token({"sub": "user123"}, expires_delta=timedelta(minutes=30))
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNjE2MjM5MDIyfQ...
    """
    # 1. 复制数据（避免修改原始 dict）
    to_encode: dict[str, Any] = data.copy()

    # 2. 计算过期时间
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        # 使用配置的默认过期时间
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 3. 添加过期时间到 payload（JWT 标准字段）
    to_encode.update({"exp": expire})

    # 4. 生成 JWT token
    # jwt.encode() 会自动添加 header {"alg": "HS256", "typ": "JWT"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    解码和验证 JWT access token

    工作原理：
    1. 使用 SECRET_KEY 验证签名
    2. 自动检查 token 是否过期（exp claim）
    3. 解码 payload 数据
    4. 异常处理（过期、无效、篡改）

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload 数据（dict），如果 token 无效则返回 None

    异常处理：
    - JWTError：token 格式错误、签名验证失败、已过期等
    - 所有异常统一返回 None（调用方负责处理认证失败）

    验证步骤：
    1. 分割 token 为 header.payload.signature
    2. 重新计算签名并对比（防篡改）
    3. 检查 exp < now()（防过期）
    4. 解码 payload（Base64 解码）

    示例：
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_access_token(token)
        >>> print(payload)
        {'sub': 'user123', 'exp': 1616239022}

        >>> # 无效 token
        >>> decode_access_token("invalid.token.here")
        None
    """
    try:
        # jwt.decode() 会自动：
        # 1. 验证签名（使用 SECRET_KEY）
        # 2. 检查过期时间（exp claim）
        # 3. 解码 payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # Token 无效、过期、篡改等情况统一返回 None
        # 具体错误信息可以通过日志记录（生产环境）
        return None
