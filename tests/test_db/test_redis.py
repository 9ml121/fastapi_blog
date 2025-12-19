# tests/test_db/test_redis.py
"""
Redis 模块测试

测试验证码的存储、获取、删除功能
"""

from app.db.redis_client import (
    delete_verification_code,
    get_redis_client,
    get_verification_code,
    save_verification_code,
)


class TestRedisConnection:
    """Redis 连接测试"""

    def test_redis_ping(self):
        """测试 Redis 连接是否正常"""
        client = get_redis_client()
        result = client.ping()
        assert result is True


class TestVerificationCode:
    """验证码功能测试"""

    # 测试用邮箱
    TEST_EMAIL = "test@example.com"
    TEST_CODE = "123456"

    def teardown_method(self):
        """每个测试方法后清理数据"""
        delete_verification_code(self.TEST_EMAIL)

    def test_save_and_get_code(self):
        """测试存储和获取验证码"""
        # 存储
        save_verification_code(self.TEST_EMAIL, self.TEST_CODE)

        # 获取
        result = get_verification_code(self.TEST_EMAIL)

        assert result == self.TEST_CODE

    def test_get_nonexistent_code(self):
        """测试获取不存在的验证码"""
        result = get_verification_code("nonexistent@example.com")
        assert result is None

    def test_delete_code(self):
        """测试删除验证码"""
        # 先存储
        save_verification_code(self.TEST_EMAIL, self.TEST_CODE)

        # 删除
        delete_verification_code(self.TEST_EMAIL)

        # 验证已删除
        result = get_verification_code(self.TEST_EMAIL)
        assert result is None
