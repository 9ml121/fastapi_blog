"""
数据库模块初始化文件

导出主要的数据库组件，便于其他模块使用
**扁平化导出**：核心组件少，扁平化合适
"""

from .database import (
    Base,
    SessionLocal,
    create_all_tables,
    drop_all_tables,
    engine,
    get_db,
)

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "create_all_tables",
    "drop_all_tables",
]
