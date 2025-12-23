"""
Redis 连接管理模块
用于存储邮箱验证码等临时数据
"""

import secrets
import string

import redis

from app.core.config import get_settings


# todo: 生产环境可考虑使用连接池优化性能
def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端实例, 每次调用都创建新连接（简单方案）

    Returns:
        Redis 客户端对象
    """
    settings = get_settings()
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,  # Redis 数据库编号（0-15）
        decode_responses=True,  # 关键：自动将 bytes 解码为 str
    )


# 验证码有效期配置（秒）
VERIFY_CODE_EXPIRE = 300  # 5分钟 = 300秒
VERIFY_CODE_PREFIX = "verify_code"


def generate_verification_code(length: int = 6) -> str:
    """生成随机验证码(默认 6 位)

    - random 模块是伪随机数生成器，可被预测，不适合安全敏感场景
    - 这里使用 secrets 模块（专为安全设计）
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def save_verification_code(email: str, code: str) -> None:
    """存储验证码到 Redis

    Args:
        email -- 用户邮箱（作为 key 的一部分）
        code -- 6位验证码

    - Key 格式: verify_code:user@example.com
    - TTL: 300秒后自动删除
    """
    client = get_redis_client()
    # setex = SET + EXPIRE 的组合命令
    # 参数顺序：key, 过期秒数, value
    client.setex(f"{VERIFY_CODE_PREFIX}:{email}", VERIFY_CODE_EXPIRE, code)


def get_verification_code(email: str) -> str | None:
    """获取验证码（用于校验）"""
    client = get_redis_client()
    return client.get(f"{VERIFY_CODE_PREFIX}:{email}")  # type: ignore


def delete_verification_code(email: str) -> None:
    """删除验证码（验证成功后调用）"""
    client = get_redis_client()
    client.delete(f"{VERIFY_CODE_PREFIX}:{email}")


def verify_code(email: str, code: str) -> bool:
    """验证用户提交的验证码是否正确

    逻辑：
    1. 从 Redis 获取存储的验证码
    2. 如果不存在（过期）或不匹配，返回 False
    3. 如果匹配，立即删除 Redis 中的验证码（防止重放）并返回 True
    """
    stored_code = get_verification_code(email)
    if stored_code and stored_code == code:
        delete_verification_code(email)
        return True

    return False
