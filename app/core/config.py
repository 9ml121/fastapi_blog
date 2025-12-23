from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类，使用 Pydantic Settings
    优先级：系统环境变量 > .env 文件 > 代码默认值
    """

    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "user"
    DATABASE_PASSWORD: str = "change-this-password"  # 占位符
    DATABASE_NAME: str = "dbname"

    # Redis 配置，开发环境没有设置密码
    REDIS_HOST: str = (
        "localhost"  # 开发环境用 localhost，生产环境可能是 redis 或内网 IP
    )
    REDIS_PORT: int = 6379  # Redis 默认端口

    # 应用配置
    APP_NAME: str = "InkFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # 安全配置
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    # Token 过期时间配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 默认1天
    ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER: int = 60 * 24 * 30  # 记住我 30天

    # 邮件配置 (SMTP)
    MAIL_USERNAME: str = ""  # 邮箱账号
    MAIL_PASSWORD: SecretStr = SecretStr("")  # 邮箱授权码 (不是登录密码)
    MAIL_FROM: str = ""  # 发件人邮箱 (通常同 username)
    MAIL_PORT: int = 465  # 端口 (163 SSL 一般用 465)
    MAIL_SERVER: str = "smtp.163.com"
    MAIL_FROM_NAME: str = APP_NAME
    MAIL_STARTTLS: bool = False  # SSL 连接通常关闭 StartTLS
    MAIL_SSL_TLS: bool = True  # 开启 SSL
    USE_CREDENTIALS: bool = True  # 使用账号密码登录
    VALIDATE_CERTS: bool = True  # 验证证书

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,  # 环境变量名不区分大小写
        "extra": "ignore",  # 关键：忽略 .env 中多余的字段（如 PYTHONPATH）
    }


# 创建全局配置实例
settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """获取配置实例的工厂函数
    这样设计便于测试时替换配置，符合 FastAPI 依赖注入模式
    """
    return settings
