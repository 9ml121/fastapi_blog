from typing import Any, TypeVar

from sqlalchemy import asc, desc, func, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.exceptions import InvalidParametersError
from app.db.database import Base
from app.schemas.common import PaginationParams

# SQLAlchemy 模型类型（如 Post）
ModelType = TypeVar("ModelType", bound=Base)


def _get_sortable_columns(model: type[ModelType]) -> dict[str, Any]:
    """动态获取sqlalchemy模型的可排序字段,排除关系字段和其他非列属性，防止 SQL 注入。

    Args:
        model: SQLAlchemy 模型类

    Returns:
        dict: {字段名: 列对象} 的映射
    """
    sortable_fields = {}

    # 使用 SQLAlchemy 的 inspect 获取模型的列信息
    mapper = inspect(model)

    # 只包含真正的数据库列
    for column in mapper.columns:
        sortable_fields[column.name] = column

    return sortable_fields


def _apply_safe_sorting(
    query: Select[tuple[ModelType]],
    model: type[ModelType],
    sort_field: str,
    sort_order: str,
) -> Select[tuple[ModelType]]:
    """安全地应用排序

    通过模型反射验证排序字段是否为真实的数据库列，
    防止 SQL 注入和访问非法字段。

    Args:
        query: SQLAlchemy 查询对象
        model: SQLAlchemy 模型类
        sort_field: 排序字段名
        sort_order: 排序方向 ('asc' 或 'desc')

    Returns:
        添加排序的查询对象

    Raises:
        ValueError: 如果字段不存在或不可排序

    Example:
        >>> query = select(Post)
        >>> query = apply_safe_sorting(query, Post, "created_at", "desc")
    """
    # 动态获取可排序字段
    sortable_fields = _get_sortable_columns(model)

    if sort_field not in sortable_fields:
        available_fields = ", ".join(sorted(sortable_fields.keys()))
        raise InvalidParametersError(
            message=f"排序字段 '{sort_field}' 不存在。可用字段: {available_fields}"
        )

    # 获取列对象
    column = sortable_fields[sort_field]

    # 应用排序
    if sort_order == "desc":
        query = query.order_by(desc(column))
    else:
        query = query.order_by(asc(column))

    return query


def paginate_query(
    db: Session,
    query: Select[tuple[ModelType]],
    params: PaginationParams,
    model: type[ModelType],
    *,
    count_query: Select[tuple[int]] | None = None,
) -> tuple[list[ModelType], int]:
    """执行分页查询（Offset-based, 支持安全排序）

    Args:
        db: 数据库会话
        query: 基础查询（SQLAlchemy select 对象）
        params: 分页参数
        model: 模型类（用于验证排序字段）
        count_query: 可选的自定义计数查询

    Returns:
        tuple: (items, total) - 数据列表和总记录数

    Raises:
        InvalidParametersError: 如果排序字段不合法

    Example:
        >>> # 基础用法
        >>> query = select(Post)
        >>> items, total = paginate_query(db, query, params, model=Post)

        >>> # 自定义计数查询（性能优化）
        >>> count_query = select(func.count(Post.id))
        >>> items, total = paginate_query(
        ...     db, query, params, model=Post, count_query=count_query
        ... )
    """
    # 应用安全排序(如果有错误，_apply_safe_sorting 会抛出 InvalidParametersError)
    query = _apply_safe_sorting(query, model, params.sort, params.order)

    # 获取总数
    if count_query is None:
        # 使用子查询避免重复的 JOIN 和 WHERE 条件
        count_query = select(func.count()).select_from(query.subquery())

    total = db.execute(count_query).scalar() or 0

    # 应用分页
    paginated_query = query.offset(params.offset).limit(params.limit)
    items = list(db.execute(paginated_query).scalars().all())

    return items, total
