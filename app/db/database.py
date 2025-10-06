"""
数据库连接配置模块

这个模块负责：
1. 创建 SQLAlchemy 引擎 (Engine)
2. 配置数据库会话工厂 (SessionLocal)
3. 定义声明式基类 (Base)
4. 提供数据库会话的依赖注入函数
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

# 获取配置
settings = get_settings()

# 创建 SQLAlchemy 引擎
# echo=True 在开发环境下打印 SQL 语句，便于调试
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境下显示 SQL 语句
    pool_pre_ping=True,  # 连接前测试连接有效性
    pool_recycle=300,  # 5分钟后回收连接，避免长时间空闲连接
)

# 创建会话工厂
# autocommit=False: 需要手动提交事务
# autoflush=False: 需要手动刷新到数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 创建声明式基类
# 所有数据库模型都将继承这个基类
# ⚠️ 20251003：可以新增 继承MappedAsDataclass， 帮助 ide 做智能提示。但是目前不是很完善，后续可以考虑采用 sqlmode 框架
# 参考：https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#declarative-dataclass-mapping
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入函数

    这个函数将被 FastAPI 的依赖注入系统使用：
    - 自动创建数据库会话
    - 在请求结束时自动关闭会话
    - 异常时自动回滚事务

    使用方式：
    @app.get("/users/")
    def read_users(db: Session = Depends(get_db)):
        return crud.get_users(db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    创建所有数据库表

    注意：在生产环境中，我们会使用 Alembic 进行数据库迁移
    这个函数主要用于开发和测试环境
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """
    删除所有数据库表

    警告：这个函数会删除所有数据，仅用于开发和测试环境
    """
    Base.metadata.drop_all(bind=engine)
