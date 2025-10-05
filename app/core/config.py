from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    使用 Pydantic Settings 自动读取环境变量
    """

    # 数据库配置 - 必须通过环境变量提供（生产环境安全）
    # 开发环境：从 .env 文件读取
    # 生产环境：从系统环境变量读取
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"  # 占位符
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "user"
    DATABASE_PASSWORD: str = "change-this-password"  # 占位符
    DATABASE_NAME: str = "dbname"

    # 应用配置
    APP_NAME: str = "FastAPI 博客系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 安全配置 - 提供默认值但建议在生产环境修改
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,  # 环境变量名不区分大小写
    }


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例的工厂函数
    这样设计便于测试时替换配置
    """
    return settings
