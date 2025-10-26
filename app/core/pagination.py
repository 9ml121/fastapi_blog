"""
通用分页工具

提供：
1. 分页参数模型（PaginationParams）
2. 分页响应模型（PaginatedResponse）
3. 分页查询函数（paginate_query）
4. 安全排序函数（apply_safe_sorting） -目前只支持单字段排序

使用示例：
    params = PaginationParams(page=1, size=20, sort="created_at", order="desc")
    items, total = paginate_query(db, query, params, model=Post)
    response = PaginatedResponse.create(items, total, params)
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import asc, desc, func, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.exceptions import InvalidParametersError
from app.db.database import Base

# 分页响应中数据项的类型， 可以是 SQLAlchemy 模型或 Pydantic 模型
ItemType = TypeVar("ItemType")
# SQLAlchemy 模型类型（如 Post）
ModelType = TypeVar("ModelType", bound=Base)


class PaginationParams(BaseModel):
    """分页查询参数

    Attributes:
        page: 页码（从1开始）
        size: 每页数量（1-100）
        sort: 排序字段
        order: 排序方向（asc/desc）

    """

    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    size: int = Field(default=20, ge=1, le=100, description="每页数量（1-100）")
    sort: str = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")

    @property
    def offset(self) -> int:
        """计算 OFFSET 值"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """获取 LIMIT 值"""
        return self.size


class PaginatedResponse(BaseModel, Generic[ItemType]):
    """分页响应格式

    Attributes:
        items: 数据列表,泛型支持
        total: 总记录数
        page: 当前页码
        size: 每页数量
        pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页

    继承：
    1. BaseModel - Pydantic 数据验证
    2. Generic[ItemType] - 泛型支持，可以是 sqlalchemy 模型或 pydantic 模型
    """

    items: list[ItemType] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        items: list[ItemType],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[ItemType]":
        """创建分页响应

        Args:
            items: 数据列表
            total: 总记录数
            params: 分页参数

        Returns:
            PaginatedResponse: 分页响应对象
        """
        # 计算总页数（向上取整）
        pages = (total + params.size - 1) // params.size if total > 0 else 0

        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )


def _get_sortable_columns(model: type[ModelType]) -> dict[str, Any]:
    """动态获取模型的可排序字段

    使用 SQLAlchemy 的 inspect 功能，只返回真正的数据库列，
    排除关系字段和其他非列属性，防止 SQL 注入。

    Args:
        model: SQLAlchemy 模型类

    Returns:
        dict: {字段名: 列对象} 的映射

    Example:
        >>> sortable = _get_sortable_columns(Post)
        >>> print(sortable.keys())
        dict_keys(['id', 'title', 'content', 'created_at', 'updated_at'])
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
    try:
        # 应用安全排序
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

    except ValueError as e:
        # 排序字段验证失败，重新抛出
        raise InvalidParametersError(message=str(e)) from e
