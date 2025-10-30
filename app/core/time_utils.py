"""统一的 UTC 时间工具函数

此模块的目标：
- 项目内所有当前时间的获取都通过这里完成，确保返回 aware datetime
- 兼容 SQLite 这类不带时区信息的数据库输出，通过补齐 tzinfo
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """获取当前 UTC 时间（aware datetime）。"""
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """确保 datetime 对象带有 UTC 时区信息。

    如果传入的是 naive datetime（tzinfo 为 None），默认认为它已经是 UTC，补齐 tzinfo。
    若本身已带时区，则保持原样返回。
    """

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
