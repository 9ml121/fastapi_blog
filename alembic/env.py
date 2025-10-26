from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 🔥 导入项目配置和数据库 Base
from app.core.config import settings
from app.db.database import Base

# 🔥 必须导入所有模型，否则 Alembic 检测不到表定义！
from app.models import *  # noqa: F403

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 🔥 注意：不使用 config.set_main_option() 来避免 ConfigParser 的 % 插值问题
# 我们会在 run_migrations_offline/online 函数中直接使用 settings.DATABASE_URL

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔥 设置目标元数据（包含所有表定义）
# Alembic 通过这个 metadata 对象获取所有模型的表结构
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # 🔥 直接使用项目配置的数据库 URL
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 🔥 最佳实践：比较选项
        compare_type=True,  # 检测列类型变化
        compare_server_default=True,  # 检测服务端默认值变化
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 🔥 使用项目配置的数据库 URL 创建引擎
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 避免迁移时的连接池问题
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 🔥 最佳实践：比较选项
            compare_type=True,  # 检测列类型变化
            compare_server_default=True,  # 检测服务端默认值变化
            # 🔥 最佳实践：事务模式（PostgreSQL 支持 DDL 事务）
            transaction_per_migration=True,  # 每个迁移一个事务，便于回滚
            # 🔥 最佳实践：渲染选项
            render_as_batch=False,  # PostgreSQL 不需要 batch 模式（SQLite 需要）
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
